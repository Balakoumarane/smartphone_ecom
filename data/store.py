
"""
data/store.py  —  DB-backed singleton Store
"""
from data.database import Database


# ─────────────────────────────────────────────────────────────────────────────
class DBList(list):
    """
    A list subclass that calls a save-callback whenever .append() is called.
    This lets GUI code do store.payments.append(payment) and have it auto-save.
    """
    def __init__(self, items, save_fn):
        super().__init__(items)
        self._save_fn = save_fn

    def append(self, item):
        super().append(item)
        self._save_fn(item)


# ─────────────────────────────────────────────────────────────────────────────
def _new(cls):
    """Create a model instance without calling __init__ (for DB reconstruction)."""
    import builtins
    return builtins.object.__new__(cls)


# ─────────────────────────────────────────────────────────────────────────────
class Store:
    """Singleton Store backed by SQLite."""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.db = Database()
        self.db.connect()

        if self.db.is_empty():
            self.db.seed()

        self._load()

    # ─────────────────────────────────────────────────────────────────────────
    #  LOAD  everything from DB into memory
    # ─────────────────────────────────────────────────────────────────────────
    def _load(self):
        self._load_smartphones()
        self._load_categories()
        self._load_users()          # also loads carts
        self._load_orders()
        self._load_payments()
        self._load_invoices()
        self._load_shipments()
        self.reports = []

    # ── Smartphones ───────────────────────────────────────────────────────────
    def _load_smartphones(self):
        from models.smartphone import Smartphone
        phones = []
        for r in self.db.load_smartphones_raw():
            p = _new(Smartphone)
            p.phone_id         = r["phone_id"]
            p.brand            = r["brand"]
            p.model            = r["model"]
            p.price            = r["price"]
            p.storage          = r["storage"]
            p.ram              = r["ram"]
            p.battery_capacity = r["battery_capacity"]
            p.camera_spec      = r["camera_spec"]
            p.display_size     = r["display_size"]
            p.operating_system = r["operating_system"]
            p.stock_quantity   = r["stock_quantity"]
            phones.append(p)
        self._phones_by_id = {p.phone_id: p for p in phones}
        self.smartphones = DBList(phones, self._on_smartphone_append)

    def _on_smartphone_append(self, phone):
        self.db.save_smartphone(phone)
        self._phones_by_id[phone.phone_id] = phone

    # ── Categories ────────────────────────────────────────────────────────────
    def _load_categories(self):
        from models.smartphone import Category
        cats = []
        for r in self.db.load_categories_raw():
            c = _new(Category)
            c.category_id   = r["category_id"]
            c.category_name = r["category_name"]
            c.description   = r["description"]
            ids = self.db.load_phone_ids_for_category(c.category_id)
            c.product_list  = [self._phones_by_id[pid]
                               for pid in ids if pid in self._phones_by_id]
            cats.append(c)
        self.categories = cats

    # ── Users ─────────────────────────────────────────────────────────────────
    def _load_users(self):
        from models.user import Customer, Admin
        from models.cart import Cart, CartItem
        from datetime import date
        users = []
        for r in self.db.load_users_raw():
            role = r["role"]
            if role == "admin":
                u = _new(Admin)
                u.user_id          = r["user_id"]
                u.admin_id         = r["user_id"]
                u.name             = r["name"]
                u.email            = r["email"]
                u.phone_number     = r["phone_number"]
                u.password         = r["password"]
                u.address          = r["address"]
                u.account_status   = r["account_status"]
                u.registration_date = date.fromisoformat(r["registration_date"])
                u.role             = "admin"
                u.permissions      = "full"
            else:
                ex = self.db.load_customer_extra(r["user_id"])
                u = _new(Customer)
                u.user_id          = r["user_id"]
                u.customer_id      = r["user_id"]
                u.name             = r["name"]
                u.email            = r["email"]
                u.phone_number     = r["phone_number"]
                u.password         = r["password"]
                u.address          = r["address"]
                u.account_status   = r["account_status"]
                u.registration_date = date.fromisoformat(r["registration_date"])
                u.shipping_address = ex["shipping_address"] if ex else r["address"]
                u.loyalty_points   = ex["loyalty_points"]   if ex else 0
                u.order_history    = []

                # Reconstruct cart
                cart_row = self.db.load_cart_raw(u.user_id)
                if cart_row:
                    cart = _new(Cart)
                    cart.cart_id     = cart_row["cart_id"]
                    cart.customer    = u
                    cart.total_price = 0.0
                    from datetime import date as _d
                    cart.created_date = _d.fromisoformat(cart_row["created_date"])
                    cart.items = []
                    for ci_row in self.db.load_cart_items_raw(cart_row["cart_id"]):
                        phone = self._phones_by_id.get(ci_row["phone_id"])
                        if phone:
                            ci = _new(CartItem)
                            ci.cart_item_id = ci_row["cart_item_id"]
                            ci.smartphone   = phone
                            ci.quantity     = ci_row["quantity"]
                            ci.price        = ci_row["price"]
                            ci.subtotal     = ci_row["subtotal"]
                            cart.items.append(ci)
                    cart.calculate_total()
                    u.cart = cart
                else:
                    # Create a fresh cart and save it
                    cart = Cart(u)
                    u.cart = cart
                    self.db.save_cart(cart)
            users.append(u)
        self.users = DBList(users, self._on_user_append)
        self._users_by_id = {u.user_id: u for u in users}

    def _on_user_append(self, user):
        from models.user import Customer, Admin
        role = "customer" if isinstance(user, Customer) else "admin"
        self.db.save_user(user, role)
        self._users_by_id[user.user_id] = user
        if isinstance(user, Customer) and user.cart:
            self.db.save_cart(user.cart)

    # ── Orders ────────────────────────────────────────────────────────────────
    def _load_orders(self):
        from models.order import Order, OrderItem
        from datetime import date
        orders = []
        for r in self.db.load_orders_raw():
            customer = self._users_by_id.get(r["customer_id"])
            if not customer:
                continue

            o = _new(Order)
            o.order_id       = r["order_id"]
            o.customer       = customer
            o.order_date     = date.fromisoformat(r["order_date"])
            o.order_status   = r["order_status"]
            o.total_amount   = r["total_amount"]
            o.shipping_address = r["shipping_address"]
            o.order_items    = []

            for oi_row in self.db.load_order_items_raw(o.order_id):
                phone = self._phones_by_id.get(oi_row["phone_id"])
                if phone:
                    oi = _new(OrderItem)
                    oi.order_item_id = oi_row["order_item_id"]
                    oi.smartphone    = phone
                    oi.quantity      = oi_row["quantity"]
                    oi.price         = oi_row["price"]
                    oi.subtotal      = oi_row["subtotal"]
                    o.order_items.append(oi)

            # Attach to customer's history
            if hasattr(customer, "order_history"):
                customer.order_history.append(o)
            orders.append(o)

        self._orders_by_id = {o.order_id: o for o in orders}
        self.orders = DBList(orders, self._on_order_append)

    def _on_order_append(self, order):
        """Called when a new order is placed. Saves order, items, stock, cart."""
        self.db.save_order(order)
        for item in order.order_items:
            self.db.save_order_item(order.order_id, item)
            # Stock was already reduced in Order.__init__ — persist it
            self.db.update_smartphone_stock(item.smartphone)
        # Clear cart in DB (cart.clear_cart() already cleared in memory)
        self.db.clear_cart_items(order.customer.user_id)
        self._orders_by_id[order.order_id] = order

    # ── Payments ──────────────────────────────────────────────────────────────
    def _load_payments(self):
        from models.payment import Payment
        from datetime import date
        payments = []
        for r in self.db.load_payments_raw():
            order = self._orders_by_id.get(r["order_id"])
            if not order:
                continue
            p = _new(Payment)
            p.payment_id            = r["payment_id"]
            p.order                 = order
            p.payment_method        = r["payment_method"]
            p.payment_status        = r["payment_status"]
            p.transaction_date      = date.fromisoformat(r["transaction_date"])
            p.transaction_reference = r["transaction_reference"]
            payments.append(p)
        self.payments = DBList(payments, self.db.save_payment)

    # ── Invoices ──────────────────────────────────────────────────────────────
    def _load_invoices(self):
        from models.invoice import Invoice
        from datetime import date
        invoices = []
        for r in self.db.load_invoices_raw():
            order = self._orders_by_id.get(r["order_id"])
            if not order:
                continue
            inv = _new(Invoice)
            inv.invoice_id   = r["invoice_id"]
            inv.order        = order
            inv.billing_date = date.fromisoformat(r["billing_date"])
            inv.tax_amount   = r["tax_amount"]
            inv.discount     = r["discount"]
            inv.total_amount = r["total_amount"]
            invoices.append(inv)
        self.invoices = DBList(invoices, self.db.save_invoice)

    # ── Shipments ─────────────────────────────────────────────────────────────
    def _load_shipments(self):
        from models.shipment import Shipment
        from datetime import date
        shipments = []
        for r in self.db.load_shipments_raw():
            order = self._orders_by_id.get(r["order_id"])
            if not order:
                continue
            s = _new(Shipment)
            s.shipment_id        = r["shipment_id"]
            s.order              = order
            s.courier_name       = r["courier_name"]
            s.tracking_number    = r["tracking_number"]
            s.shipment_status    = r["shipment_status"]
            s.estimated_delivery = date.fromisoformat(r["estimated_delivery"])
            shipments.append(s)
        self.shipments = DBList(shipments, self.db.save_shipment)

    # ─────────────────────────────────────────────────────────────────────────
    #  PUBLIC SAVE HELPERS  (called by GUI after mutations)
    # ─────────────────────────────────────────────────────────────────────────
    def save_customer(self, customer):
        """Persist loyalty points, shipping address, profile, status."""
        self.db.update_user(customer)

    def save_order_status(self, order):
        """Persist order status after change (update / cancel)."""
        self.db.update_order_status(order)

    def save_stock(self, smartphones):
        """Persist stock for a list of Smartphone objects (after cancel)."""
        for phone in smartphones:
            self.db.update_smartphone_stock(phone)

    def save_smartphone(self, phone):
        """Persist a smartphone (after admin edit)."""
        self.db.save_smartphone(phone)

    def delete_smartphone(self, phone_id):
        """Delete a smartphone from DB and in-memory list."""
        self.db.delete_smartphone(phone_id)
        # Remove from in-memory list (bypass DBList to avoid re-save)
        list.clear(self.smartphones)
        list.extend(self.smartphones,
                    [p for p in self._phones_by_id.values()
                     if p.phone_id != phone_id])
        self._phones_by_id.pop(phone_id, None)
        # Remove from categories
        for cat in self.categories:
            cat.product_list = [p for p in cat.product_list
                                if p.phone_id != phone_id]

    def save_shipment(self, shipment):
        """Persist shipment status change."""
        self.db.update_shipment(shipment)

    def save_cart(self, customer):
        """Persist current cart items for a customer."""
        cart = customer.cart
        if not cart:
            return
        self.db.clear_cart_items(customer.user_id)
        for item in cart.items:
            self.db.save_cart_item(cart.cart_id, item)

    # ─────────────────────────────────────────────────────────────────────────
    #  LOOKUP HELPERS  (same interface as before)
    # ─────────────────────────────────────────────────────────────────────────
    def get_user_by_email(self, email):
        return next((u for u in self.users if u.email == email), None)

    def get_customer_by_email(self, email):
        from models.user import Customer
        return next((u for u in self.users
                     if isinstance(u, Customer) and u.email == email), None)

    def get_admin_by_email(self, email):
        from models.user import Admin
        return next((u for u in self.users
                     if isinstance(u, Admin) and u.email == email), None)

class Session:
    current_user = None

    @classmethod
    def login(cls, user):
        cls.current_user = user

    @classmethod
    def logout(cls):
        cls.current_user = None

    @classmethod
    def get_user(cls):
        return cls.current_user