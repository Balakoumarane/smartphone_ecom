"""
data/database.py
================
SQLite database layer for SmartShop.
Handles all table creation, CRUD operations, and seeding.
The DB file  smartshop.db  is stored in the  data/  folder.
"""

import sqlite3
import os
from datetime import date, timedelta
import random

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "smartshop.db")


class Database:
    """
    Singleton SQLite manager.
    All GUI and Store code accesses data through this class.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._conn = None
        return cls._instance

    # ─────────────────────────────────────────────────────────────────────────
    #  CONNECTION
    # ─────────────────────────────────────────────────────────────────────────
    def connect(self):
        if self._conn is None:
            self._conn = sqlite3.connect(DB_PATH, check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA foreign_keys = ON")
            self._conn.execute("PRAGMA journal_mode = WAL")
            self._create_tables()
        return self._conn

    @property
    def conn(self):
        return self.connect()

    def _ex(self, sql, params=()):
        """Execute and commit."""
        self.conn.execute(sql, params)
        self.conn.commit()

    def _q(self, sql, params=()):
        """Query and return all rows."""
        return self.conn.execute(sql, params).fetchall()

    def _q1(self, sql, params=()):
        """Query and return one row."""
        return self.conn.execute(sql, params).fetchone()

    def _ensure_column(self, table_name, column_name, definition):
        cols = {
            row["name"]
            for row in self.conn.execute(f"PRAGMA table_info({table_name})").fetchall()
        }
        if column_name not in cols:
            self.conn.execute(
                f"ALTER TABLE {table_name} ADD COLUMN {column_name} {definition}"
            )
            self.conn.commit()

    # ─────────────────────────────────────────────────────────────────────────
    #  TABLE CREATION
    # ─────────────────────────────────────────────────────────────────────────
    def _create_tables(self):
        stmts = [
            # ── Users ────────────────────────────────────────────────────────
            """CREATE TABLE IF NOT EXISTS users (
                user_id           TEXT PRIMARY KEY,
                name              TEXT NOT NULL,
                email             TEXT NOT NULL UNIQUE,
                phone_number      TEXT,
                password          TEXT NOT NULL,
                address           TEXT DEFAULT '',
                account_status    TEXT DEFAULT 'active',
                registration_date TEXT,
                role              TEXT NOT NULL   -- 'customer' or 'admin'
            )""",

            # ── Customers (extends users) ─────────────────────────────────────
            """CREATE TABLE IF NOT EXISTS customers (
                customer_id      TEXT PRIMARY KEY REFERENCES users(user_id),
                shipping_address TEXT DEFAULT '',
                loyalty_points   INTEGER DEFAULT 0
            )""",

            # ── Smartphones ───────────────────────────────────────────────────
            """CREATE TABLE IF NOT EXISTS smartphones (
                phone_id         TEXT PRIMARY KEY,
                brand            TEXT NOT NULL,
                model            TEXT NOT NULL,
                price            REAL NOT NULL,
                storage          TEXT,
                ram              TEXT,
                battery_capacity INTEGER,
                camera_spec      TEXT,
                display_size     REAL,
                operating_system TEXT,
                stock_quantity   INTEGER DEFAULT 0
            )""",

            # ── Categories ────────────────────────────────────────────────────
            """CREATE TABLE IF NOT EXISTS categories (
                category_id   TEXT PRIMARY KEY,
                category_name TEXT NOT NULL,
                description   TEXT DEFAULT ''
            )""",

            # ── Category ↔ Smartphone (many-to-many) ─────────────────────────
            """CREATE TABLE IF NOT EXISTS category_phones (
                category_id TEXT REFERENCES categories(category_id),
                phone_id    TEXT REFERENCES smartphones(phone_id),
                PRIMARY KEY (category_id, phone_id)
            )""",

            # ── Carts ─────────────────────────────────────────────────────────
            """CREATE TABLE IF NOT EXISTS carts (
                cart_id      TEXT PRIMARY KEY,
                customer_id  TEXT REFERENCES users(user_id),
                created_date TEXT
            )""",

            # ── Cart Items ────────────────────────────────────────────────────
            """CREATE TABLE IF NOT EXISTS cart_items (
                cart_item_id TEXT PRIMARY KEY,
                cart_id      TEXT REFERENCES carts(cart_id),
                phone_id     TEXT REFERENCES smartphones(phone_id),
                quantity     INTEGER,
                price        REAL,
                subtotal     REAL
            )""",

            # ── Orders ────────────────────────────────────────────────────────
            """CREATE TABLE IF NOT EXISTS orders (
                order_id         TEXT PRIMARY KEY,
                customer_id      TEXT REFERENCES users(user_id),
                order_date       TEXT,
                order_status     TEXT DEFAULT 'Pending',
                total_amount     REAL,
                shipping_address TEXT,
                loyalty_points_used INTEGER DEFAULT 0,
                loyalty_discount REAL DEFAULT 0,
                loyalty_points_earned INTEGER DEFAULT 0,
                loyalty_points_awarded INTEGER DEFAULT 0
            )""",

            # ── Order Items ───────────────────────────────────────────────────
            """CREATE TABLE IF NOT EXISTS order_items (
                order_item_id TEXT PRIMARY KEY,
                order_id      TEXT REFERENCES orders(order_id),
                phone_id      TEXT REFERENCES smartphones(phone_id),
                quantity      INTEGER,
                price         REAL,
                subtotal      REAL
            )""",

            # ── Payments ──────────────────────────────────────────────────────
            """CREATE TABLE IF NOT EXISTS payments (
                payment_id            TEXT PRIMARY KEY,
                order_id              TEXT REFERENCES orders(order_id),
                payment_method        TEXT,
                payment_status        TEXT DEFAULT 'Pending',
                transaction_date      TEXT,
                transaction_reference TEXT,
                gateway_name          TEXT DEFAULT '',
                payment_details       TEXT DEFAULT '',
                payment_note          TEXT DEFAULT '',
                verification_status   TEXT DEFAULT 'Pending',
                verified_by           TEXT DEFAULT '',
                verified_at           TEXT DEFAULT '',
                refund_status         TEXT DEFAULT 'Not Requested',
                refund_method         TEXT DEFAULT '',
                refund_details        TEXT DEFAULT '',
                refund_requested_at   TEXT DEFAULT '',
                refund_reference      TEXT DEFAULT '',
                refund_processed_by   TEXT DEFAULT '',
                refund_processed_at   TEXT DEFAULT ''
            )""",

            # ── Invoices ──────────────────────────────────────────────────────
            """CREATE TABLE IF NOT EXISTS invoices (
                invoice_id   TEXT PRIMARY KEY,
                order_id     TEXT REFERENCES orders(order_id),
                billing_date TEXT,
                tax_amount   REAL,
                discount     REAL,
                total_amount REAL
            )""",

            # ── Shipments ─────────────────────────────────────────────────────
            """CREATE TABLE IF NOT EXISTS shipments (
                shipment_id        TEXT PRIMARY KEY,
                order_id           TEXT REFERENCES orders(order_id),
                courier_name       TEXT,
                tracking_number    TEXT,
                shipment_status    TEXT,
                estimated_delivery TEXT,
                delivered_date     TEXT DEFAULT ''
            )""",

            # -- Wishlist --
            """CREATE TABLE IF NOT EXISTS wishlists (
                customer_id TEXT REFERENCES users(user_id) ON DELETE CASCADE,
                phone_id    TEXT REFERENCES smartphones(phone_id) ON DELETE CASCADE,
                added_date  TEXT,
                PRIMARY KEY (customer_id, phone_id)
            )""",

            # -- Coupons --
            """CREATE TABLE IF NOT EXISTS coupons (
                coupon_id        TEXT PRIMARY KEY,
                code             TEXT NOT NULL UNIQUE,
                discount_percent REAL NOT NULL,
                is_active        INTEGER DEFAULT 1,
                created_date     TEXT
            )""",
        ]
        for stmt in stmts:
            self.conn.execute(stmt)
        self.conn.commit()
        for name, definition in [
            ("loyalty_points_used", "INTEGER DEFAULT 0"),
            ("loyalty_discount", "REAL DEFAULT 0"),
            ("loyalty_points_earned", "INTEGER DEFAULT 0"),
            ("loyalty_points_awarded", "INTEGER DEFAULT 0"),
        ]:
            self._ensure_column("orders", name, definition)
        for name, definition in [
            ("gateway_name", "TEXT DEFAULT ''"),
            ("payment_details", "TEXT DEFAULT ''"),
            ("payment_note", "TEXT DEFAULT ''"),
            ("verification_status", "TEXT DEFAULT 'Pending'"),
            ("verified_by", "TEXT DEFAULT ''"),
            ("verified_at", "TEXT DEFAULT ''"),
            ("refund_status", "TEXT DEFAULT 'Not Requested'"),
            ("refund_method", "TEXT DEFAULT ''"),
            ("refund_details", "TEXT DEFAULT ''"),
            ("refund_requested_at", "TEXT DEFAULT ''"),
            ("refund_reference", "TEXT DEFAULT ''"),
            ("refund_processed_by", "TEXT DEFAULT ''"),
            ("refund_processed_at", "TEXT DEFAULT ''"),
        ]:
            self._ensure_column("payments", name, definition)
        self._ensure_column("shipments", "delivered_date", "TEXT DEFAULT ''")

    # ─────────────────────────────────────────────────────────────────────────
    #  SEED CHECK
    # ─────────────────────────────────────────────────────────────────────────
    def is_empty(self):
        row = self._q1("SELECT COUNT(*) as cnt FROM smartphones")
        return row["cnt"] == 0

    # ─────────────────────────────────────────────────────────────────────────
    #  USERS
    # ─────────────────────────────────────────────────────────────────────────
    def save_user(self, user, role):
        self._ex("""
            INSERT OR REPLACE INTO users
              (user_id, name, email, phone_number, password,
               address, account_status, registration_date, role)
            VALUES (?,?,?,?,?,?,?,?,?)
        """, (user.user_id, user.name, user.email, user.phone_number,
              user.password, user.address, user.account_status,
              str(user.registration_date), role))

        if role == "customer":
            self._ex("""
                INSERT OR REPLACE INTO customers
                  (customer_id, shipping_address, loyalty_points)
                VALUES (?,?,?)
            """, (user.user_id,
                  getattr(user, "shipping_address", user.address),
                  getattr(user, "loyalty_points", 0)))

    def update_user(self, user):
        """Persist profile / status / password changes."""
        self._ex("""
            UPDATE users SET name=?, email=?, phone_number=?,
              password=?, address=?, account_status=?
            WHERE user_id=?
        """, (user.name, user.email, user.phone_number,
              user.password, user.address, user.account_status,
              user.user_id))
        if hasattr(user, "loyalty_points"):
            self._ex("""
                UPDATE customers SET shipping_address=?, loyalty_points=?
                WHERE customer_id=?
            """, (getattr(user, "shipping_address", user.address),
                  user.loyalty_points, user.user_id))

    def load_users_raw(self):
        return self._q("SELECT * FROM users")

    def load_customer_extra(self, customer_id):
        return self._q1(
            "SELECT * FROM customers WHERE customer_id=?", (customer_id,))

    # ─────────────────────────────────────────────────────────────────────────
    #  SMARTPHONES
    # ─────────────────────────────────────────────────────────────────────────
    def save_smartphone(self, phone):
        self._ex("""
            INSERT OR REPLACE INTO smartphones
              (phone_id, brand, model, price, storage, ram,
               battery_capacity, camera_spec, display_size,
               operating_system, stock_quantity)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """, (phone.phone_id, phone.brand, phone.model, phone.price,
              phone.storage, phone.ram, phone.battery_capacity,
              phone.camera_spec, phone.display_size,
              phone.operating_system, phone.stock_quantity))

    def update_smartphone_stock(self, phone):
        self._ex(
            "UPDATE smartphones SET stock_quantity=? WHERE phone_id=?",
            (phone.stock_quantity, phone.phone_id))

    def delete_smartphone(self, phone_id):
        self._ex("DELETE FROM wishlists WHERE phone_id=?", (phone_id,))
        self._ex("DELETE FROM category_phones WHERE phone_id=?", (phone_id,))
        self._ex("DELETE FROM smartphones WHERE phone_id=?", (phone_id,))

    def load_smartphones_raw(self):
        return self._q("SELECT * FROM smartphones")

    # ─────────────────────────────────────────────────────────────────────────
    #  CATEGORIES
    # ─────────────────────────────────────────────────────────────────────────
    def save_category(self, cat):
        self._ex("""
            INSERT OR REPLACE INTO categories (category_id, category_name, description)
            VALUES (?,?,?)
        """, (cat.category_id, cat.category_name, cat.description))

    def link_phone_to_category(self, category_id, phone_id):
        self._ex("""
            INSERT OR IGNORE INTO category_phones (category_id, phone_id)
            VALUES (?,?)
        """, (category_id, phone_id))

    def load_categories_raw(self):
        return self._q("SELECT * FROM categories")

    def load_phone_ids_for_category(self, category_id):
        rows = self._q(
            "SELECT phone_id FROM category_phones WHERE category_id=?",
            (category_id,))
        return [r["phone_id"] for r in rows]

    def add_wishlist_item(self, customer_id, phone_id):
        self._ex("""
            INSERT OR IGNORE INTO wishlists (customer_id, phone_id, added_date)
            VALUES (?,?,?)
        """, (customer_id, phone_id, str(date.today())))

    def remove_wishlist_item(self, customer_id, phone_id):
        self._ex(
            "DELETE FROM wishlists WHERE customer_id=? AND phone_id=?",
            (customer_id, phone_id),
        )

    def load_wishlist_raw(self, customer_id):
        return self._q(
            "SELECT * FROM wishlists WHERE customer_id=? ORDER BY added_date DESC",
            (customer_id,),
        )

    def save_coupon(self, coupon):
        self._ex(
            """
            INSERT OR REPLACE INTO coupons
              (coupon_id, code, discount_percent, is_active, created_date)
            VALUES (?,?,?,?,?)
            """,
            (
                coupon.coupon_id,
                coupon.code,
                coupon.discount_percent,
                1 if coupon.is_active else 0,
                str(coupon.created_date),
            ),
        )

    def load_coupons_raw(self):
        return self._q("SELECT * FROM coupons ORDER BY code ASC")

    def delete_coupon(self, coupon_id):
        self._ex("DELETE FROM coupons WHERE coupon_id=?", (coupon_id,))

    # ─────────────────────────────────────────────────────────────────────────
    #  CARTS
    # ─────────────────────────────────────────────────────────────────────────
    def save_cart(self, cart):
        self._ex("""
            INSERT OR REPLACE INTO carts (cart_id, customer_id, created_date)
            VALUES (?,?,?)
        """, (cart.cart_id, cart.customer.user_id, str(cart.created_date)))

    def save_cart_item(self, cart_id, item):
        self._ex("""
            INSERT OR REPLACE INTO cart_items
              (cart_item_id, cart_id, phone_id, quantity, price, subtotal)
            VALUES (?,?,?,?,?,?)
        """, (item.cart_item_id, cart_id, item.smartphone.phone_id,
              item.quantity, item.price, item.subtotal))

    def clear_cart_items(self, customer_id):
        row = self._q1(
            "SELECT cart_id FROM carts WHERE customer_id=?", (customer_id,))
        if row:
            self._ex("DELETE FROM cart_items WHERE cart_id=?", (row["cart_id"],))

    def load_cart_raw(self, customer_id):
        return self._q1(
            "SELECT * FROM carts WHERE customer_id=?", (customer_id,))

    def load_cart_items_raw(self, cart_id):
        return self._q(
            "SELECT * FROM cart_items WHERE cart_id=?", (cart_id,))

    # ─────────────────────────────────────────────────────────────────────────
    #  ORDERS
    # ─────────────────────────────────────────────────────────────────────────
    def save_order(self, order):
        self._ex("""
            INSERT OR REPLACE INTO orders
              (order_id, customer_id, order_date, order_status,
               total_amount, shipping_address, loyalty_points_used,
               loyalty_discount, loyalty_points_earned, loyalty_points_awarded)
            VALUES (?,?,?,?,?,?,?,?,?,?)
        """, (order.order_id, order.customer.user_id,
              str(order.order_date), order.order_status,
              order.total_amount, order.shipping_address,
              order.loyalty_points_used, order.loyalty_discount,
              order.loyalty_points_earned, order.loyalty_points_awarded))

    def save_order_item(self, order_id, item):
        self._ex("""
            INSERT OR REPLACE INTO order_items
              (order_item_id, order_id, phone_id, quantity, price, subtotal)
            VALUES (?,?,?,?,?,?)
        """, (item.order_item_id, order_id, item.smartphone.phone_id,
              item.quantity, item.price, item.subtotal))

    def update_order_status(self, order):
        self._ex(
            """
            UPDATE orders
            SET order_status=?, loyalty_points_used=?, loyalty_discount=?,
                loyalty_points_earned=?, loyalty_points_awarded=?
            WHERE order_id=?
            """,
            (
                order.order_status,
                order.loyalty_points_used,
                order.loyalty_discount,
                order.loyalty_points_earned,
                order.loyalty_points_awarded,
                order.order_id,
            ),
        )

    def load_orders_raw(self):
        return self._q("SELECT * FROM orders ORDER BY order_date ASC")

    def load_order_items_raw(self, order_id):
        return self._q(
            "SELECT * FROM order_items WHERE order_id=?", (order_id,))

    # ─────────────────────────────────────────────────────────────────────────
    #  PAYMENTS
    # ─────────────────────────────────────────────────────────────────────────
    def save_payment(self, payment):
        self._ex("""
            INSERT OR REPLACE INTO payments
              (payment_id, order_id, payment_method, payment_status,
               transaction_date, transaction_reference, gateway_name,
               payment_details, payment_note, verification_status,
               verified_by, verified_at, refund_status, refund_method,
               refund_details, refund_requested_at, refund_reference,
               refund_processed_by, refund_processed_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (payment.payment_id, payment.order.order_id,
              payment.payment_method, payment.payment_status,
              str(payment.transaction_date), payment.transaction_reference,
              payment.gateway_name, payment.payment_details, payment.payment_note,
              payment.verification_status, payment.verified_by,
              payment.verified_at, payment.refund_status,
              payment.refund_method, payment.refund_details,
              payment.refund_requested_at, payment.refund_reference,
              payment.refund_processed_by, payment.refund_processed_at))

    def load_payments_raw(self):
        return self._q("SELECT * FROM payments")

    # ─────────────────────────────────────────────────────────────────────────
    #  INVOICES
    # ─────────────────────────────────────────────────────────────────────────
    def save_invoice(self, invoice):
        self._ex("""
            INSERT OR REPLACE INTO invoices
              (invoice_id, order_id, billing_date, tax_amount,
               discount, total_amount)
            VALUES (?,?,?,?,?,?)
        """, (invoice.invoice_id, invoice.order.order_id,
              str(invoice.billing_date), invoice.tax_amount,
              invoice.discount, invoice.total_amount))

    def load_invoices_raw(self):
        return self._q("SELECT * FROM invoices")

    # ─────────────────────────────────────────────────────────────────────────
    #  SHIPMENTS
    # ─────────────────────────────────────────────────────────────────────────
    def save_shipment(self, shipment):
        self._ex("""
            INSERT OR REPLACE INTO shipments
              (shipment_id, order_id, courier_name, tracking_number,
               shipment_status, estimated_delivery, delivered_date)
            VALUES (?,?,?,?,?,?,?)
        """, (shipment.shipment_id, shipment.order.order_id,
              shipment.courier_name, shipment.tracking_number,
              shipment.shipment_status, str(shipment.estimated_delivery),
              str(shipment.delivered_date) if shipment.delivered_date else ""))

    def update_shipment(self, shipment):
        self._ex(
            """
            UPDATE shipments
            SET shipment_status=?, estimated_delivery=?, delivered_date=?
            WHERE shipment_id=?
            """,
            (
                shipment.shipment_status,
                str(shipment.estimated_delivery),
                str(shipment.delivered_date) if shipment.delivered_date else "",
                shipment.shipment_id,
            ),
        )

    def load_shipments_raw(self):
        return self._q("SELECT * FROM shipments")

    # ─────────────────────────────────────────────────────────────────────────
    #  SEED DATA  (39 real phones, INR pricing)
    # ─────────────────────────────────────────────────────────────────────────
    def seed(self):
        """Insert default phones, categories, admin and demo customer."""
        import uuid as _uuid
        from datetime import date as _date

        # ── Admin ─────────────────────────────────────────────────────────────
        admin_id = str(_uuid.uuid4())[:8]
        self._ex("""
            INSERT OR IGNORE INTO users
              (user_id, name, email, phone_number, password,
               address, account_status, registration_date, role)
            VALUES (?,?,?,?,?,?,?,?,?)
        """, (admin_id, "Admin User", "admin@store.com", "0000000000",
              "admin123", "", "active", str(_date.today()), "admin"))

        # ── Demo Customer ──────────────────────────────────────────────────────
        cust_id = str(_uuid.uuid4())[:8]
        self._ex("""
            INSERT OR IGNORE INTO users
              (user_id, name, email, phone_number, password,
               address, account_status, registration_date, role)
            VALUES (?,?,?,?,?,?,?,?,?)
        """, (cust_id, "Arjun Kumar", "arjun@email.com", "9876543210",
              "pass123", "12 Anna Nagar, Chennai, TN 600040",
              "active", str(_date.today()), "customer"))
        self._ex("""
            INSERT OR IGNORE INTO customers (customer_id, shipping_address, loyalty_points)
            VALUES (?,?,?)
        """, (cust_id, "12 Anna Nagar, Chennai, TN 600040", 0))

        # Cart for demo customer
        cart_id = str(_uuid.uuid4())[:8]
        self._ex("""
            INSERT OR IGNORE INTO carts (cart_id, customer_id, created_date)
            VALUES (?,?,?)
        """, (cart_id, cust_id, str(_date.today())))

        self._ex(
            """
            INSERT OR IGNORE INTO coupons
              (coupon_id, code, discount_percent, is_active, created_date)
            VALUES (?,?,?,?,?)
            """,
            ("DEFAULT10", "SAVE10", 10.0, 1, str(_date.today())),
        )

        # ── Smartphones (39 real phones, INR) ─────────────────────────────────
        phones_data = [
            # (brand, model, price_inr, storage, ram, battery, camera, display, os, stock)
            ("Samsung",  "Galaxy S26 Ultra",   139999, "512GB", "12GB", 5000, "200MP+10MP+50MP+50MP Rear, 12MP Front",  6.9,  "Android 15", 20),
            ("Samsung",  "Galaxy S26 Plus",    119999, "256GB", "12GB", 4900, "50MP+12MP+10MP Rear, 12MP Front",        6.7,  "Android 15", 18),
            ("Samsung",  "Galaxy S26",          87999, "256GB", "12GB", 4300, "50MP+12MP+10MP Rear, 12MP Front",        6.3,  "Android 15", 25),
            ("Vivo",     "X300 Pro",           109998, "256GB", "16GB", 6510, "50MP+50MP+200MP Rear, 50MP Front",       6.78, "Android 15", 15),
            ("realme",   "GT 8 Pro",            72999, "256GB", "12GB", 7000, "50MP+50MP+200MP Rear, 32MP Front",       6.79, "Android 15", 20),
            ("OnePlus",  "15",                  72999, "256GB", "12GB", 7300, "50MP+50MP+50MP Rear, 32MP Front",        6.78, "Android 15", 22),
            ("Samsung",  "Galaxy S25",          74999, "256GB", "12GB", 4000, "50MP+12MP+10MP Rear, 12MP Front",        6.2,  "Android 15", 30),
            ("Samsung",  "Galaxy S25 Ultra",   104990, "256GB", "12GB", 5000, "200MP+50MP+10MP+50MP Rear, 12MP Front", 6.9,  "Android 15", 18),
            ("Vivo",     "X300",                75998, "256GB", "12GB", 6040, "200MP+50MP+50MP Rear, 50MP Front",       6.31, "Android 15", 20),
            ("iQOO",     "15",                  72998, "256GB", "12GB", 7000, "50MP+50MP+50MP Rear, 32MP Front",        6.85, "Android 15", 15),
            ("Apple",    "iPhone 17 Pro Max",  149900, "512GB", "12GB", 4832, "48MP+48MP+48MP Rear, 18MP Front",        6.9,  "iOS 18",     25),
            ("Samsung",  "Galaxy Z Fold7",     174999, "512GB", "12GB", 4400, "200MP+12MP+10MP Rear, 10MP Front",       8.0,  "Android 15", 10),
            ("Samsung",  "Galaxy S25 Plus",     73999, "256GB", "12GB", 4900, "50MP+12MP+10MP Rear, 12MP Front",        6.7,  "Android 15", 22),
            ("realme",   "GT 7 Pro",            49998, "256GB", "12GB", 5800, "50MP+8MP+50MP Rear, 16MP Front",         6.78, "Android 15", 25),
            ("Motorola", "Signature",           53049, "256GB", "12GB", 5200, "50MP+50MP+50MP Rear, 50MP Front",        6.8,  "Android 15", 12),
            ("Apple",    "iPhone Air",          93499, "256GB",  "8GB", 3149, "48MP Rear, 18MP Front",                  6.5,  "iOS 18",     20),
            ("OnePlus",  "13",                  60999, "256GB", "12GB", 6000, "50MP+50MP+50MP Rear, 32MP Front",        6.82, "Android 15", 28),
            ("OnePlus",  "15R",                 47997, "256GB", "12GB", 7400, "50MP+8MP Rear, 32MP Front",              6.83, "Android 15", 30),
            ("Oppo",     "Find X9",             74999, "256GB", "12GB", 7025, "50MP+50MP+50MP+2MP Rear, 32MP Front",   6.59, "Android 15", 15),
            ("OnePlus",  "13s",                 50997, "256GB", "12GB", 5850, "50MP+50MP Rear, 32MP Front",             6.32, "Android 15", 20),
            ("Motorola", "Razr 60 Ultra",       79999, "256GB", "16GB", 4700, "50MP+50MP Rear, 50MP Front",             6.96, "Android 15", 10),
            ("iQOO",     "15R",                 44998, "256GB",  "8GB", 7600, "50MP+8MP Rear, 32MP Front",              6.59, "Android 15", 20),
            ("Vivo",     "X200T",               59999, "256GB", "12GB", 6200, "50MP+50MP+50MP Rear, 32MP Front",        6.67, "Android 15", 18),
            ("Oppo",     "Find X9 Pro",        109999, "256GB", "16GB", 7500, "50MP+50MP+200MP+2MP Rear, 50MP Front",  6.78, "Android 15", 12),
            ("Apple",    "iPhone 17",           82900, "256GB",  "8GB", 3692, "48MP+48MP Rear, 18MP Front",             6.3,  "iOS 18",     35),
            ("Nothing",  "Phone 4a",            31999, "256GB",  "8GB", 5400, "50MP+50MP+8MP Rear, 32MP Front",         6.78, "Android 15", 30),
            ("realme",   "GT 7",                34999, "256GB",  "8GB", 7000, "50MP+8MP+50MP Rear, 32MP Front",         6.78, "Android 15", 28),
            ("Vivo",     "T4 Ultra",            37990, "256GB",  "8GB", 5500, "50MP+8MP+50MP Rear, 32MP Front",         6.67, "Android 15", 25),
            ("POCO",     "F7",                  35999, "256GB", "12GB", 7550, "50MP+8MP Rear, 20MP Front",              6.83, "Android 15", 22),
            ("POCO",     "X7 Pro",              23999, "256GB",  "8GB", 6550, "50MP+8MP Rear, 20MP Front",              6.67, "Android 15", 35),
            ("OnePlus",  "13R",                 39996, "256GB", "12GB", 6000, "50MP+8MP+50MP Rear, 16MP Front",         6.78, "Android 15", 28),
            ("Samsung",  "Galaxy S24 FE",       39898, "256GB",  "8GB", 4700, "50MP+12MP+8MP Rear, 10MP Front",         6.7,  "Android 15", 30),
            ("Oppo",     "K13 Turbo 5G",        26594, "128GB",  "8GB", 7000, "50MP+2MP Rear, 16MP Front",              6.8,  "Android 15", 35),
            ("Oppo",     "K13 Turbo Pro",       34999, "256GB",  "8GB", 7000, "50MP+2MP Rear, 16MP Front",              6.8,  "Android 15", 28),
            ("realme",   "GT 7T",               30899, "256GB",  "8GB", 7000, "50MP+8MP Rear, 32MP Front",              6.8,  "Android 15", 30),
            ("POCO",     "F6",                  29999, "256GB",  "8GB", 5000, "50MP+8MP Rear, 20MP Front",              6.67, "Android 15", 32),
            ("iQOO",     "Neo 10",              32990, "256GB",  "8GB", 7000, "50MP+8MP Rear, 32MP Front",              6.78, "Android 15", 25),
            ("iQOO",     "Neo 9 Pro",           38989, "256GB",  "8GB", 5160, "50MP+8MP Rear, 16MP Front",              6.78, "Android 15", 20),
            ("realme",   "GT 6",                27999, "256GB",  "8GB", 5500, "50MP+8MP+50MP Rear, 32MP Front",         6.78, "Android 15", 30),
        ]

        phone_ids = []
        for (brand, model, price, storage, ram, battery, camera, disp, os, stock) in phones_data:
            pid = str(_uuid.uuid4())[:8]
            phone_ids.append((pid, brand, model, price))
            self._ex("""
                INSERT OR IGNORE INTO smartphones
                  (phone_id, brand, model, price, storage, ram,
                   battery_capacity, camera_spec, display_size,
                   operating_system, stock_quantity)
                VALUES (?,?,?,?,?,?,?,?,?,?,?)
            """, (pid, brand, model, float(price), storage, ram, battery,
                  camera, disp, os, stock))

        # ── Categories ────────────────────────────────────────────────────────
        def make_cat(name, desc):
            cid = str(_uuid.uuid4())[:8]
            self._ex("""
                INSERT OR IGNORE INTO categories (category_id, category_name, description)
                VALUES (?,?,?)
            """, (cid, name, desc))
            return cid

        def link(cid, pid):
            self._ex("""
                INSERT OR IGNORE INTO category_phones (category_id, phone_id)
                VALUES (?,?)
            """, (cid, pid))

        # Build index: brand → phone_ids
        brand_idx = {}
        price_idx = {}
        for pid, brand, model, price in phone_ids:
            brand_idx.setdefault(brand, []).append(pid)
            price_idx[pid] = price

        # Flagship  > ₹80,000
        flagship_id = make_cat("Flagship", "Premium smartphones above ₹80,000")
        for pid, _, _, price in phone_ids:
            if price >= 80000:
                link(flagship_id, pid)

        # Upper Mid  ₹50,000 – ₹80,000
        upper_id = make_cat("Upper Mid-Range", "Great performers ₹50,000–₹80,000")
        for pid, _, _, price in phone_ids:
            if 50000 <= price < 80000:
                link(upper_id, pid)

        # Mid-Range  ₹30,000 – ₹50,000
        mid_id = make_cat("Mid-Range", "Best value ₹30,000–₹50,000")
        for pid, _, _, price in phone_ids:
            if 30000 <= price < 50000:
                link(mid_id, pid)

        # Budget  < ₹30,000
        budget_id = make_cat("Budget", "Affordable smartphones under ₹30,000")
        for pid, _, _, price in phone_ids:
            if price < 30000:
                link(budget_id, pid)

        # Apple iPhones
        apple_id = make_cat("Apple iPhones", "iPhone lineup — iOS 18")
        for pid in brand_idx.get("Apple", []):
            link(apple_id, pid)

        # Samsung Galaxy
        samsung_id = make_cat("Samsung Galaxy", "Full Samsung smartphone range")
        for pid in brand_idx.get("Samsung", []):
            link(samsung_id, pid)

        # OnePlus
        oneplus_id = make_cat("OnePlus", "Speed, performance and value")
        for pid in brand_idx.get("OnePlus", []):
            link(oneplus_id, pid)

        self.conn.commit()
        print("[DB] Seed complete —",
              len(phones_data), "phones,",
              "7 categories, admin + demo customer.")
