import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from data.store import Session
from gui.payment_workflows import (
    CardPaymentDialog,
    NetBankingDialog,
    RefundRequestDialog,
    UPIPaymentDialog,
)
from gui.theme import COLORS, FONTS
from models.invoice import Invoice
from models.payment import Payment
from models.shipment import Shipment
from utils.document_export import export_invoice_document


def format_inr(amount):
    return f"Rs {amount:,.0f}"


class CustomerPortal:
    STATUS_COLORS = {
        "Pending": "#FEF3C7",
        "Processing": "#DBEAFE",
        "Shipped": "#E0F2FE",
        "Delivered": "#DCFCE7",
        "Cancelled": "#FEE2E2",
    }

    def __init__(self, customer, store):
        self.customer = customer
        self.store = store
        self._current_view = self._show_browse

        self.root = tk.Toplevel()
        self.root.title(f"SmartShop - Welcome, {customer.name}")
        self.root.geometry("1120x700")
        self.root.configure(bg=COLORS["bg"])
        self.root.protocol("WM_DELETE_WINDOW", self.root.destroy)
        self._center()
        self._build_shell()
        self._show_browse()

    def _center(self):
        w, h = 1120, 700
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        self.root.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}")

    def _restore_home_window(self):
        home = self.root.master
        if home and home is not self.root and home.winfo_exists():
            home.deiconify()
            home.lift()
            home.focus_force()

    def logout(self):
        if not messagebox.askyesno("Logout", "Are you sure you want to logout?", parent=self.root):
            return
        self._restore_home_window()
        Session.logout()
        self.root.destroy()

    def _build_shell(self):
        topbar = tk.Frame(self.root, bg=COLORS["sidebar"], height=56)
        topbar.pack(fill="x")
        topbar.pack_propagate(False)

        tk.Label(
            topbar,
            text="SmartShop Customer",
            font=("Segoe UI", 13, "bold"),
            bg=COLORS["sidebar"],
            fg="white",
        ).pack(side="left", padx=18)

        right = tk.Frame(topbar, bg=COLORS["sidebar"])
        right.pack(side="right", padx=18)
        tk.Button(
            right,
            text="Refresh",
            font=FONTS["small"],
            bg="#1D4ED8",
            fg="white",
            relief="flat",
            padx=10,
            pady=4,
            cursor="hand2",
            command=self._refresh_view,
        ).pack(side="right")
        self._points_lbl = tk.Label(
            right,
            text="",
            font=FONTS["body"],
            bg=COLORS["sidebar"],
            fg="#BFDBFE",
        )
        self._points_lbl.pack(side="right", padx=(0, 12))
        self._update_points_label()

        sidebar = tk.Frame(self.root, bg="#1E3A5F", width=190)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        tk.Label(
            sidebar,
            text="MENU",
            font=FONTS["small"],
            bg="#1E3A5F",
            fg="#94A3B8",
        ).pack(pady=(22, 8), padx=14, anchor="w")

        nav = [
            ("Browse", self._show_browse),
            ("Wishlist", self._show_wishlist),
            ("My Cart", self._show_cart),
            ("My Orders", self._show_orders),
            ("Profile", self._show_profile),
        ]
        for text, cmd in nav:
            tk.Button(
                sidebar,
                text=text,
                font=FONTS["body"],
                bg="#1E3A5F",
                fg="white",
                relief="flat",
                anchor="w",
                padx=14,
                pady=10,
                cursor="hand2",
                activebackground=COLORS["primary"],
                activeforeground="white",
                command=cmd,
            ).pack(fill="x")

        tk.Button(
            sidebar,
            text="Logout",
            bg=COLORS["error"],
            fg="white",
            font=("Arial", 11, "bold"),
            cursor="hand2",
            command=self.logout,
        ).pack(side="bottom", pady=20, fill="x")

        self.content = tk.Frame(self.root, bg=COLORS["bg"])
        self.content.pack(side="right", fill="both", expand=True)

    def _clear(self):
        for widget in self.content.winfo_children():
            widget.destroy()

    def _refresh_view(self):
        self.store.reload()
        fresh = self.store.get_user_by_id(self.customer.user_id)
        if fresh:
            self.customer = fresh
            Session.login(self.customer)
        self._update_points_label()
        (self._current_view or self._show_browse)()

    def _update_points_label(self):
        if hasattr(self, "_points_lbl"):
            self._points_lbl.config(
                text=f"{self.customer.name} | {self.customer.loyalty_points} pts"
            )

    @staticmethod
    def _make_tree(parent, cols, widths, height=15):
        style = ttk.Style()
        style.configure(
            "SS.Treeview",
            rowheight=28,
            font=FONTS["body"],
            background=COLORS["card"],
            fieldbackground=COLORS["card"],
        )
        style.configure(
            "SS.Treeview.Heading",
            font=FONTS["subheading"],
            background=COLORS["table_header"],
        )

        wrap = tk.Frame(parent, bg=COLORS["bg"])
        tree = ttk.Treeview(wrap, columns=cols, show="headings", style="SS.Treeview", height=height)
        for col, width in zip(cols, widths):
            tree.heading(col, text=col)
            tree.column(col, width=width, anchor="center")
        scrollbar = ttk.Scrollbar(wrap, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        return wrap, tree

    def _payment_for_order(self, order_id):
        return self.store.get_payment_for_order(order_id)

    def _display_total_for_order(self, order):
        invoice = next((entry for entry in self.store.invoices if entry.order.order_id == order.order_id), None)
        return invoice.total_amount if invoice else order.total_amount

    def _show_browse(self):
        self._current_view = self._show_browse
        self._clear()

        frame = tk.Frame(self.content, bg=COLORS["bg"])
        frame.pack(fill="both", expand=True, padx=20, pady=14)

        top = tk.Frame(frame, bg=COLORS["bg"])
        top.pack(fill="x", pady=(0, 10))
        tk.Label(
            top,
            text="Browse Smartphones",
            font=FONTS["heading"],
            bg=COLORS["bg"],
            fg=COLORS["text"],
        ).pack(side="left")

        filters = tk.Frame(top, bg=COLORS["bg"])
        filters.pack(side="right")

        self._search_var = tk.StringVar()
        tk.Entry(filters, textvariable=self._search_var, font=FONTS["body"], width=20, relief="solid", bd=1).pack(side="left", ipady=4, padx=4)

        self._cat_var = tk.StringVar(value="All Categories")
        categories = ["All Categories"] + [cat.category_name for cat in self.store.categories]
        ttk.Combobox(
            filters,
            textvariable=self._cat_var,
            values=categories,
            state="readonly",
            width=16,
        ).pack(side="left", padx=4)

        tk.Button(filters, text="Search", font=FONTS["button"], bg=COLORS["primary"], fg="white", relief="flat", padx=10, cursor="hand2", command=self._filter_products).pack(side="left", padx=4)
        tk.Button(filters, text="Clear", font=FONTS["button"], bg=COLORS["border"], fg=COLORS["text"], relief="flat", padx=8, cursor="hand2", command=self._clear_filter).pack(side="left")

        cols = ("Brand", "Model", "Price", "RAM", "Storage", "OS", "Battery", "Stock")
        widths = [110, 180, 90, 70, 90, 110, 95, 70]
        wrap, self._prod_tree = self._make_tree(frame, cols, widths, height=15)
        wrap.pack(fill="both", expand=True)
        self._prod_tree.tag_configure("available", background=COLORS["table_row"])
        self._prod_tree.tag_configure("alt", background=COLORS["table_alt"])
        self._prod_tree.tag_configure("out", background="#FEE2E2", foreground="#991B1B")
        self._load_products(self.store.smartphones)

        bar = tk.Frame(frame, bg=COLORS["bg"])
        bar.pack(fill="x", pady=(10, 0))
        tk.Button(bar, text="Details", font=FONTS["button"], bg="#64748B", fg="white", relief="flat", padx=12, pady=5, cursor="hand2", command=self._view_details).pack(side="left", padx=(0, 6))
        tk.Button(bar, text="Add to Cart", font=FONTS["button"], bg=COLORS["primary"], fg="white", relief="flat", padx=12, pady=5, cursor="hand2", command=self._add_to_cart_dialog).pack(side="left", padx=(0, 6))
        tk.Button(bar, text="Add to Wishlist", font=FONTS["button"], bg=COLORS["warning"], fg="white", relief="flat", padx=12, pady=5, cursor="hand2", command=self._add_selected_to_wishlist).pack(side="left")

    def _load_products(self, phones):
        self._prod_tree.delete(*self._prod_tree.get_children())
        for idx, phone in enumerate(phones):
            tag = "out" if phone.stock_quantity <= 0 else ("available" if idx % 2 == 0 else "alt")
            stock_text = str(phone.stock_quantity) if phone.stock_quantity > 0 else "Out"
            self._prod_tree.insert(
                "",
                "end",
                iid=phone.phone_id,
                values=(
                    phone.brand,
                    phone.model,
                    format_inr(phone.price),
                    phone.ram,
                    phone.storage,
                    phone.operating_system,
                    f"{phone.battery_capacity} mAh",
                    stock_text,
                ),
                tags=(tag,),
            )

    def _filter_products(self):
        keyword = self._search_var.get().strip().lower()
        category_name = self._cat_var.get()
        phones = self.store.smartphones
        if category_name != "All Categories":
            category = next((cat for cat in self.store.categories if cat.category_name == category_name), None)
            if category:
                phones = category.get_products()
        if keyword:
            phones = [phone for phone in phones if keyword in phone.brand.lower() or keyword in phone.model.lower()]
        self._load_products(phones)

    def _clear_filter(self):
        self._search_var.set("")
        self._cat_var.set("All Categories")
        self._load_products(self.store.smartphones)

    def _selected_phone(self):
        selection = self._prod_tree.selection() if hasattr(self, "_prod_tree") else ()
        if not selection:
            messagebox.showwarning("Select Product", "Please select a product first.", parent=self.root)
            return None
        return self.store.get_phone_by_id(selection[0])

    def _view_details(self, phone=None):
        phone = phone or self._selected_phone()
        if not phone:
            return
        win = tk.Toplevel(self.root)
        win.title(f"{phone.brand} {phone.model}")
        win.geometry("500x420")
        win.configure(bg=COLORS["bg"])
        win.transient(self.root)
        win.grab_set()

        tk.Label(win, text=f"{phone.brand} {phone.model}", font=FONTS["heading"], bg=COLORS["bg"], fg=COLORS["text"]).pack(pady=(22, 4))
        tk.Label(win, text=format_inr(phone.price), font=("Segoe UI", 18, "bold"), bg=COLORS["bg"], fg=COLORS["primary"]).pack()

        card = tk.Frame(win, bg=COLORS["card"], relief="solid", bd=1, padx=18, pady=16)
        card.pack(fill="both", expand=True, padx=24, pady=16)
        details = [
            ("Operating System", phone.operating_system),
            ("RAM", phone.ram),
            ("Storage", phone.storage),
            ("Battery", f"{phone.battery_capacity} mAh"),
            ("Camera", phone.camera_spec),
            ("Display", f'{phone.display_size}"'),
            ("Availability", f"{phone.stock_quantity} units"),
        ]
        for label, value in details:
            row = tk.Frame(card, bg=COLORS["card"])
            row.pack(fill="x", pady=4)
            tk.Label(row, text=f"{label}:", font=FONTS["subheading"], bg=COLORS["card"], fg=COLORS["subtext"], width=18, anchor="w").pack(side="left")
            tk.Label(row, text=value, font=FONTS["body"], bg=COLORS["card"], fg=COLORS["text"], wraplength=240, justify="left").pack(side="left")

    def _add_to_cart_dialog(self, phone=None, remove_from_wishlist=False):
        phone = phone or self._selected_phone()
        if not phone:
            return
        if phone.stock_quantity <= 0:
            messagebox.showerror("Out of Stock", "This product is currently out of stock.", parent=self.root)
            return

        win = tk.Toplevel(self.root)
        win.title("Add to Cart")
        win.geometry("320x230")
        win.configure(bg=COLORS["bg"])
        win.transient(self.root)
        win.grab_set()

        tk.Label(win, text=f"{phone.brand} {phone.model}", font=FONTS["subheading"], bg=COLORS["bg"], fg=COLORS["text"]).pack(pady=(22, 4))
        tk.Label(win, text=f"{format_inr(phone.price)} each", font=FONTS["body"], bg=COLORS["bg"], fg=COLORS["primary"]).pack()
        tk.Label(win, text="Quantity", font=FONTS["body"], bg=COLORS["bg"], fg=COLORS["text"]).pack(pady=(18, 4))
        qty_var = tk.IntVar(value=1)
        ttk.Spinbox(win, from_=1, to=min(10, phone.stock_quantity), textvariable=qty_var, width=8, font=FONTS["body"]).pack()

        def confirm():
            qty = qty_var.get()
            if qty <= 0:
                return
            self.customer.cart.add_item(phone, qty)
            self.store.save_cart(self.customer)
            if remove_from_wishlist:
                self.store.remove_from_wishlist(self.customer, phone.phone_id)
            messagebox.showinfo("Added", f"{qty} x {phone.brand} {phone.model} added to cart.", parent=win)
            win.destroy()
            if remove_from_wishlist:
                self._show_wishlist()

        tk.Button(win, text="Add to Cart", font=FONTS["button"], bg=COLORS["primary"], fg="white", relief="flat", padx=18, pady=6, cursor="hand2", command=confirm).pack(pady=16)

    def _add_selected_to_wishlist(self):
        phone = self._selected_phone()
        if not phone:
            return
        if self.store.add_to_wishlist(self.customer, phone):
            messagebox.showinfo("Wishlist", f"{phone.brand} {phone.model} added to wishlist.", parent=self.root)
        else:
            messagebox.showinfo("Wishlist", "This product is already in your wishlist.", parent=self.root)

    def _show_wishlist(self):
        self._current_view = self._show_wishlist
        self._clear()

        frame = tk.Frame(self.content, bg=COLORS["bg"])
        frame.pack(fill="both", expand=True, padx=20, pady=14)

        tk.Label(frame, text="My Wishlist", font=FONTS["heading"], bg=COLORS["bg"], fg=COLORS["text"]).pack(anchor="w", pady=(0, 10))

        cols = ("Brand", "Model", "Price", "Storage", "Stock")
        widths = [120, 220, 100, 110, 90]
        wrap, self._wishlist_tree = self._make_tree(frame, cols, widths, height=14)
        wrap.pack(fill="both", expand=True)
        for phone in self.customer.wishlist:
            stock_text = str(phone.stock_quantity) if phone.stock_quantity > 0 else "Out"
            self._wishlist_tree.insert("", "end", iid=phone.phone_id, values=(phone.brand, phone.model, format_inr(phone.price), phone.storage, stock_text))

        bar = tk.Frame(frame, bg=COLORS["bg"])
        bar.pack(fill="x", pady=(10, 0))
        tk.Button(bar, text="Details", font=FONTS["button"], bg="#64748B", fg="white", relief="flat", padx=12, pady=5, cursor="hand2", command=self._wishlist_details).pack(side="left", padx=(0, 6))
        tk.Button(bar, text="Move to Cart", font=FONTS["button"], bg=COLORS["primary"], fg="white", relief="flat", padx=12, pady=5, cursor="hand2", command=self._move_wishlist_to_cart).pack(side="left", padx=(0, 6))
        tk.Button(bar, text="Remove", font=FONTS["button"], bg=COLORS["error"], fg="white", relief="flat", padx=12, pady=5, cursor="hand2", command=self._remove_from_wishlist).pack(side="left")

    def _selected_wishlist_phone(self):
        selection = self._wishlist_tree.selection() if hasattr(self, "_wishlist_tree") else ()
        if not selection:
            messagebox.showwarning("Select Product", "Please select a wishlist item first.", parent=self.root)
            return None
        return self.store.get_phone_by_id(selection[0])

    def _wishlist_details(self):
        phone = self._selected_wishlist_phone()
        if phone:
            self._view_details(phone)

    def _move_wishlist_to_cart(self):
        phone = self._selected_wishlist_phone()
        if not phone:
            return
        self._add_to_cart_dialog(phone, remove_from_wishlist=True)

    def _remove_from_wishlist(self):
        phone = self._selected_wishlist_phone()
        if not phone:
            return
        self.store.remove_from_wishlist(self.customer, phone.phone_id)
        self._show_wishlist()
    def _show_cart(self):
        self._current_view = self._show_cart
        self._clear()

        frame = tk.Frame(self.content, bg=COLORS["bg"])
        frame.pack(fill="both", expand=True, padx=20, pady=14)

        tk.Label(frame, text="Shopping Cart", font=FONTS["heading"], bg=COLORS["bg"], fg=COLORS["text"]).pack(anchor="w", pady=(0, 10))

        cols = ("Product", "Price", "Quantity", "Subtotal")
        widths = [320, 110, 100, 120]
        wrap, self._cart_tree = self._make_tree(frame, cols, widths, height=12)
        wrap.pack(fill="x")
        self._refresh_cart()

        bar = tk.Frame(frame, bg=COLORS["bg"])
        bar.pack(fill="x", pady=14)
        self._total_lbl = tk.Label(
            bar,
            text=f"Total: {format_inr(self.customer.cart.calculate_total())}",
            font=("Segoe UI", 13, "bold"),
            bg=COLORS["bg"],
            fg=COLORS["primary"],
        )
        self._total_lbl.pack(side="left")

        tk.Button(bar, text="Remove Selected", font=FONTS["button"], bg=COLORS["error"], fg="white", relief="flat", padx=12, pady=6, cursor="hand2", command=self._remove_cart_item).pack(side="right", padx=5)
        tk.Button(bar, text="Clear Cart", font=FONTS["button"], bg="#64748B", fg="white", relief="flat", padx=12, pady=6, cursor="hand2", command=self._clear_cart).pack(side="right", padx=5)
        tk.Button(bar, text="Checkout", font=FONTS["button"], bg=COLORS["success"], fg="white", relief="flat", padx=12, pady=6, cursor="hand2", command=self._checkout).pack(side="right", padx=5)

    def _refresh_cart(self):
        self._cart_tree.delete(*self._cart_tree.get_children())
        for item in self.customer.cart.get_cart_items():
            self._cart_tree.insert(
                "",
                "end",
                iid=item.cart_item_id,
                values=(
                    f"{item.smartphone.brand} {item.smartphone.model}",
                    format_inr(item.price),
                    item.quantity,
                    format_inr(item.subtotal),
                ),
            )

    def _remove_cart_item(self):
        selection = self._cart_tree.selection()
        if not selection:
            messagebox.showwarning("Select Item", "Please select an item to remove.", parent=self.root)
            return
        item_id = selection[0]
        item = next((entry for entry in self.customer.cart.items if entry.cart_item_id == item_id), None)
        if not item:
            return
        self.customer.cart.remove_item(item.smartphone.phone_id)
        self.store.save_cart(self.customer)
        self._refresh_cart()
        self._total_lbl.config(text=f"Total: {format_inr(self.customer.cart.calculate_total())}")

    def _clear_cart(self):
        if not messagebox.askyesno("Clear Cart", "Remove all items from your cart?", parent=self.root):
            return
        self.customer.cart.clear_cart()
        self.store.save_cart(self.customer)
        self._refresh_cart()
        self._total_lbl.config(text="Total: Rs 0")

    def _checkout(self):
        if not self.customer.cart.items:
            messagebox.showwarning("Empty Cart", "Your cart is empty.", parent=self.root)
            return
        CheckoutWindow(self.root, self.customer, self.store, self._post_checkout)

    def _post_checkout(self):
        self._refresh_view()
        self._show_orders()

    def _show_orders(self):
        self._current_view = self._show_orders
        self._clear()

        frame = tk.Frame(self.content, bg=COLORS["bg"])
        frame.pack(fill="both", expand=True, padx=20, pady=14)

        tk.Label(frame, text="My Orders", font=FONTS["heading"], bg=COLORS["bg"], fg=COLORS["text"]).pack(anchor="w", pady=(0, 10))

        cols = ("Order ID", "Date", "Items", "Total", "Status", "Payment", "Verified", "Refund")
        widths = [90, 90, 55, 90, 110, 135, 100, 100]
        wrap, self._order_tree = self._make_tree(frame, cols, widths, height=14)
        wrap.pack(fill="both", expand=True)
        self._load_orders()

        bar = tk.Frame(frame, bg=COLORS["bg"])
        bar.pack(fill="x", pady=(10, 0))
        tk.Button(bar, text="View Payment", font=FONTS["button"], bg="#0F766E", fg="white", relief="flat", padx=12, pady=6, cursor="hand2", command=self._view_payment).pack(side="left", padx=(0, 6))
        tk.Button(bar, text="View Invoice", font=FONTS["button"], bg=COLORS["primary"], fg="white", relief="flat", padx=12, pady=6, cursor="hand2", command=self._view_invoice).pack(side="left", padx=(0, 6))
        tk.Button(bar, text="Track Shipment", font=FONTS["button"], bg="#0EA5E9", fg="white", relief="flat", padx=12, pady=6, cursor="hand2", command=self._track_shipment).pack(side="left", padx=(0, 6))
        tk.Button(bar, text="Cancel Order", font=FONTS["button"], bg=COLORS["error"], fg="white", relief="flat", padx=12, pady=6, cursor="hand2", command=self._cancel_order).pack(side="left")

    def _load_orders(self):
        for status, color in self.STATUS_COLORS.items():
            self._order_tree.tag_configure(status, background=color)
        self._order_tree.delete(*self._order_tree.get_children())
        for order in reversed(self.customer.order_history):
            payment = self._payment_for_order(order.order_id)
            self._order_tree.insert(
                "",
                "end",
                iid=order.order_id,
                values=(
                    f"#{order.order_id}",
                    order.order_date,
                    len(order.order_items),
                    format_inr(self._display_total_for_order(order)),
                    order.order_status,
                    payment.payment_status if payment else "-",
                    payment.verification_label() if payment else "-",
                    payment.refund_label() if payment else "-",
                ),
                tags=(order.order_status,),
            )

    def _selected_order(self):
        selection = self._order_tree.selection() if hasattr(self, "_order_tree") else ()
        if not selection:
            messagebox.showwarning("Select Order", "Please select an order first.", parent=self.root)
            return None
        return self.store.get_order_by_id(selection[0])

    def _view_payment(self):
        order = self._selected_order()
        if not order:
            return
        payment = self._payment_for_order(order.order_id)
        if not payment:
            messagebox.showinfo("No Payment", "No payment found for this order.", parent=self.root)
            return
        lines = [payment.generate_receipt()]
        if payment.payment_note:
            lines.append(f"\nNote: {payment.payment_note}")
        messagebox.showinfo("Payment Summary", "\n".join(lines), parent=self.root)

    def _view_invoice(self):
        order = self._selected_order()
        if not order:
            return
        invoice = next((entry for entry in self.store.invoices if entry.order.order_id == order.order_id), None)
        if not invoice:
            messagebox.showinfo("No Invoice", "No invoice found for this order.", parent=self.root)
            return
        InvoiceViewer(self.root, invoice)

    def _track_shipment(self):
        order = self._selected_order()
        if not order:
            return
        shipment = next((entry for entry in self.store.shipments if entry.order.order_id == order.order_id), None)
        if not shipment:
            messagebox.showinfo("No Shipment", "Shipment has not been created yet.", parent=self.root)
            return
        messagebox.showinfo("Shipment Tracking", shipment.track_shipment(), parent=self.root)

    def _cancel_order(self):
        order = self._selected_order()
        if not order:
            return
        payment = self._payment_for_order(order.order_id)
        if not messagebox.askyesno("Cancel Order", f"Cancel order #{order.order_id}?", parent=self.root):
            return
        refund_request = RefundRequestDialog(self.root, payment).show()
        if refund_request is None:
            return
        if not order.cancel_order():
            messagebox.showerror(
                "Cannot Cancel",
                "Shipped, delivered, or already cancelled orders cannot be cancelled.",
                parent=self.root,
            )
            return
        self.store.save_order_status(order)
        self.store.save_stock([item.smartphone for item in order.order_items])
        self.store.save_customer(self.customer)
        shipment = next((entry for entry in self.store.shipments if entry.order.order_id == order.order_id), None)
        if shipment:
            shipment.update_shipment_status("Cancelled")
            self.store.save_shipment(shipment)
        if payment:
            payment.request_refund(refund_request["method"], refund_request["details"])
            if refund_request["note"]:
                payment.payment_note = refund_request["note"]
            self.store.save_payment(payment)
        messagebox.showinfo(
            "Cancelled",
            "Order cancelled successfully. Refund preference has been recorded.",
            parent=self.root,
        )
        self._show_orders()

    def _show_profile(self):
        self._current_view = self._show_profile
        self._clear()

        frame = tk.Frame(self.content, bg=COLORS["bg"])
        frame.pack(fill="both", expand=True, padx=30, pady=20)

        tk.Label(frame, text="My Profile", font=FONTS["heading"], bg=COLORS["bg"], fg=COLORS["text"]).pack(anchor="w", pady=(0, 16))

        card = tk.Frame(frame, bg=COLORS["card"], relief="solid", bd=1, padx=30, pady=20)
        card.pack(fill="x")

        display = [
            ("Name", self.customer.name, "name"),
            ("Email", self.customer.email, None),
            ("Phone", self.customer.phone_number, "phone"),
            ("Address", self.customer.shipping_address or self.customer.address, "address"),
            ("Loyalty Points", str(self.customer.loyalty_points), None),
            ("Member Since", str(self.customer.registration_date), None),
            ("Status", self.customer.account_status.title(), None),
        ]
        self._pf_vars = {}
        for label, value, key in display:
            row = tk.Frame(card, bg=COLORS["card"])
            row.pack(fill="x", pady=5)
            tk.Label(row, text=f"{label}:", font=FONTS["subheading"], bg=COLORS["card"], fg=COLORS["subtext"], width=16, anchor="w").pack(side="left")
            var = tk.StringVar(value=value)
            if key:
                self._pf_vars[key] = var
                tk.Entry(row, textvariable=var, font=FONTS["body"], relief="solid", bd=1, width=38).pack(side="left")
            else:
                tk.Label(row, textvariable=var, font=FONTS["body"], bg=COLORS["card"], fg=COLORS["text"]).pack(side="left")

        def save():
            self.customer.update_profile(
                self._pf_vars["name"].get(),
                self._pf_vars["phone"].get(),
                self._pf_vars["address"].get(),
            )
            self.customer.shipping_address = self._pf_vars["address"].get()
            self.store.save_customer(self.customer)
            self._update_points_label()
            messagebox.showinfo("Saved", "Profile updated successfully.", parent=self.root)

        tk.Button(card, text="Save Changes", font=FONTS["button"], bg=COLORS["primary"], fg="white", relief="flat", padx=16, pady=6, cursor="hand2", command=save).pack(anchor="w", pady=(14, 0))

        pw_card = tk.Frame(frame, bg=COLORS["card"], relief="solid", bd=1, padx=30, pady=16)
        pw_card.pack(fill="x", pady=(16, 0))
        tk.Label(pw_card, text="Change Password", font=FONTS["subheading"], bg=COLORS["card"], fg=COLORS["text"]).pack(anchor="w", pady=(0, 10))

        self._old_pw = tk.StringVar()
        self._new_pw = tk.StringVar()
        tk.Label(pw_card, text="Current Password", font=FONTS["small"], bg=COLORS["card"], fg=COLORS["subtext"]).pack(anchor="w")
        tk.Entry(pw_card, textvariable=self._old_pw, show="*", font=FONTS["body"], relief="solid", bd=1).pack(fill="x", ipady=4, pady=(2, 8))
        tk.Label(pw_card, text="New Password", font=FONTS["small"], bg=COLORS["card"], fg=COLORS["subtext"]).pack(anchor="w")
        tk.Entry(pw_card, textvariable=self._new_pw, show="*", font=FONTS["body"], relief="solid", bd=1).pack(fill="x", ipady=4, pady=(2, 8))

        def change_password():
            if self.customer.change_password(self._old_pw.get(), self._new_pw.get()):
                self.store.save_customer(self.customer)
                self._old_pw.set("")
                self._new_pw.set("")
                messagebox.showinfo("Done", "Password changed successfully.", parent=self.root)
            else:
                messagebox.showerror("Error", "Current password is incorrect.", parent=self.root)

        tk.Button(pw_card, text="Update Password", font=FONTS["button"], bg="#64748B", fg="white", relief="flat", padx=12, pady=5, cursor="hand2", command=change_password).pack(anchor="w", pady=8)


class CheckoutWindow:
    def __init__(self, parent, customer, store, on_done):
        self.customer = customer
        self.store = store
        self.on_done = on_done

        self.win = tk.Toplevel(parent)
        self.win.title("Checkout")
        self.win.geometry("520x600")
        self.win.configure(bg=COLORS["bg"])
        self.win.transient(parent)
        self.win.grab_set()
        self._build()

    def _build(self):
        hdr = tk.Frame(self.win, bg=COLORS["success"], height=65)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="Checkout", font=FONTS["heading"], bg=COLORS["success"], fg="white").pack(expand=True)

        summary = tk.Frame(self.win, bg=COLORS["secondary"], relief="solid", bd=1, padx=16, pady=10)
        summary.pack(fill="x", padx=22, pady=12)
        tk.Label(summary, text="Order Summary", font=FONTS["subheading"], bg=COLORS["secondary"], fg=COLORS["text"]).pack(anchor="w")
        for item in self.customer.cart.items:
            tk.Label(
                summary,
                text=f"{item.smartphone.brand} {item.smartphone.model} x{item.quantity} - {format_inr(item.subtotal)}",
                font=FONTS["body"],
                bg=COLORS["secondary"],
                fg=COLORS["text"],
            ).pack(anchor="w", pady=1)

        self._subtotal = self.customer.cart.calculate_total()
        self._discount_code = tk.StringVar()
        self._addr = tk.StringVar(value=self.customer.shipping_address)
        self._pay_method = tk.StringVar(value="Credit Card")
        self._use_loyalty = tk.BooleanVar(value=False)

        form = tk.Frame(self.win, bg=COLORS["bg"], padx=22)
        form.pack(fill="both", expand=True)

        tk.Label(form, text="Shipping Address", font=FONTS["subheading"], bg=COLORS["bg"], fg=COLORS["text"]).pack(anchor="w", pady=(8, 2))
        tk.Entry(form, textvariable=self._addr, font=FONTS["body"], relief="solid", bd=1).pack(fill="x", ipady=6)

        tk.Label(form, text="Payment Method", font=FONTS["subheading"], bg=COLORS["bg"], fg=COLORS["text"]).pack(anchor="w", pady=(10, 2))
        ttk.Combobox(
            form,
            textvariable=self._pay_method,
            values=["Credit Card", "Debit Card", "UPI", "Net Banking", "Cash on Delivery"],
            state="readonly",
            font=FONTS["body"],
        ).pack(fill="x", ipady=4)

        tk.Label(form, text="Discount Code", font=FONTS["subheading"], bg=COLORS["bg"], fg=COLORS["text"]).pack(anchor="w", pady=(10, 2))
        tk.Entry(form, textvariable=self._discount_code, font=FONTS["body"], relief="solid", bd=1).pack(fill="x", ipady=5)
        tk.Label(
            form,
            text=self._available_coupon_text(),
            font=FONTS["small"],
            bg=COLORS["bg"],
            fg=COLORS["subtext"],
            justify="left",
            wraplength=440,
        ).pack(anchor="w", pady=(2, 10))

        eligible_loyalty_points = (self.customer.loyalty_points // 100) * 100
        if eligible_loyalty_points:
            tk.Checkbutton(
                form,
                text=(
                    f"Use loyalty points ({eligible_loyalty_points} pts -> "
                    f"{format_inr((eligible_loyalty_points // 100) * 10.0)} off)"
                ),
                variable=self._use_loyalty,
                font=FONTS["body"],
                bg=COLORS["bg"],
                fg=COLORS["text"],
                activebackground=COLORS["bg"],
                activeforeground=COLORS["text"],
                selectcolor=COLORS["secondary"],
                command=self._update_price_preview,
            ).pack(anchor="w", pady=(0, 10))
        else:
            tk.Label(
                form,
                text=f"Loyalty Points Available: {self.customer.loyalty_points} (need 100 points for Rs 10 off)",
                font=FONTS["small"],
                bg=COLORS["bg"],
                fg=COLORS["subtext"],
            ).pack(anchor="w", pady=(0, 10))

        self._price_lbl = tk.Label(form, text="", font=FONTS["body"], bg=COLORS["bg"], fg=COLORS["text"], justify="left")
        self._price_lbl.pack(anchor="w")
        self._update_price_preview()
        self._discount_code.trace_add("write", lambda *_: self._update_price_preview())
        self._use_loyalty.trace_add("write", lambda *_: self._update_price_preview())

        tk.Button(
            self.win,
            text="Place Order",
            font=("Segoe UI", 11, "bold"),
            bg=COLORS["success"],
            fg="white",
            relief="flat",
            pady=10,
            cursor="hand2",
            command=self._place,
        ).pack(fill="x", padx=22, pady=16)

    def _available_coupon_text(self):
        active_coupons = self.store.get_active_coupons()
        if not active_coupons:
            return "No active coupon codes available right now."
        return "Available Coupons: " + ", ".join(
            f"{coupon.code} ({coupon.discount_percent:g}% off)"
            for coupon in active_coupons
        )

    def _entered_coupon(self):
        code = self._discount_code.get().strip().upper()
        if not code:
            return None
        return self.store.get_coupon_by_code(code)

    def _applied_coupon(self):
        code = self._discount_code.get().strip().upper()
        if not code:
            return None
        return self.store.get_coupon_by_code(code, active_only=True)

    def _discount_amount(self):
        coupon = self._applied_coupon()
        return coupon.calculate_discount(self._subtotal) if coupon else 0.0

    def _coupon_status_text(self):
        code = self._discount_code.get().strip().upper()
        if not code:
            return "Coupon: Not applied"
        coupon = self._entered_coupon()
        if not coupon:
            return f"Coupon: {code} not found"
        if not coupon.is_active:
            return f"Coupon: {code} is inactive"
        return f"Coupon: {coupon.code} applied ({coupon.discount_percent:g}% off)"

    def _loyalty_points_to_use(self):
        if not self._use_loyalty.get():
            return 0
        return (self.customer.loyalty_points // 100) * 100

    def _loyalty_discount_amount(self):
        return (self._loyalty_points_to_use() // 100) * 10.0

    def _final_total(self):
        discount = self._discount_amount() + self._loyalty_discount_amount()
        taxable = max(self._subtotal - discount, 0)
        tax = round(taxable * Invoice.TAX_RATE, 2)
        return round(taxable + tax, 2)

    def _update_price_preview(self):
        code_discount = self._discount_amount()
        loyalty_discount = self._loyalty_discount_amount()
        total = self._final_total()
        loyalty_points_used = self._loyalty_points_to_use()
        available_loyalty_points = self.customer.loyalty_points
        self._price_lbl.config(
            text=(
                f"Subtotal: {format_inr(self._subtotal)}\n"
                f"{self._coupon_status_text()}\n"
                f"Coupon Discount: {format_inr(code_discount)}\n"
                f"Loyalty Available: {available_loyalty_points} pts\n"
                f"Loyalty Used: {loyalty_points_used} pts -> {format_inr(loyalty_discount)}\n"
                f"Estimated Total (incl. tax): {format_inr(total)}"
            )
        )

    def _collect_payment_data(self, final_total):
        method = self._pay_method.get()
        if method == "UPI":
            return UPIPaymentDialog(self.win, final_total).show()
        if method in {"Credit Card", "Debit Card"}:
            return CardPaymentDialog(self.win, final_total, method).show()
        if method == "Net Banking":
            return NetBankingDialog(self.win, final_total).show()
        return {
            "gateway_name": "Cash Collection",
            "payment_details": f"Customer selected cash on delivery for {format_inr(final_total)}.",
            "transaction_reference": f"COD-{self.customer.user_id.upper()}",
            "note": "Awaiting payment collection during delivery.",
        }

    def _place(self):
        address = self._addr.get().strip()
        if not address:
            messagebox.showerror("Error", "Please enter a shipping address.", parent=self.win)
            return
        self._update_price_preview()
        entered_code = self._discount_code.get().strip().upper()
        if entered_code and not self._applied_coupon():
            messagebox.showerror("Invalid Coupon", "Please use an active valid coupon code.", parent=self.win)
            return
        final_total = self._final_total()
        payment_data = self._collect_payment_data(final_total)
        if payment_data is None:
            return

        self.customer.shipping_address = address
        order = self.customer.place_order(self.store)
        if not order:
            messagebox.showerror("Error", "Failed to place the order.", parent=self.win)
            return

        payment = Payment(order, self._pay_method.get())
        payment.process_payment(final_total, **payment_data)
        self.store.save_payment(payment)

        code_discount = self._discount_amount()
        loyalty_points_used = self._loyalty_points_to_use()
        loyalty_discount = self._loyalty_discount_amount()
        total_discount = code_discount + loyalty_discount
        order.apply_loyalty_redemption(loyalty_points_used, loyalty_discount)
        if loyalty_points_used:
            self.customer.loyalty_points -= loyalty_points_used
        invoice = Invoice(order, discount=total_discount)
        order.set_loyalty_earnings(int(invoice.total_amount // 100))
        self.store.invoices.append(invoice)

        shipment = Shipment(order)
        self.store.shipments.append(shipment)

        self.store.save_customer(self.customer)
        self.store.save_order_status(order)

        messagebox.showinfo(
            "Order Confirmed",
            (
                f"Order #{order.order_id} placed successfully.\n\n"
                f"Final Total: {format_inr(invoice.total_amount)}\n"
                f"Loyalty Used: {loyalty_points_used} pts\n"
                f"Loyalty To Earn On Delivery: {order.loyalty_points_earned} pts\n"
                f"Payment Status: {payment.payment_status}\n"
                f"Verification: {payment.verification_status}\n"
                f"Courier: {shipment.courier_name}\n"
                f"Tracking: {shipment.tracking_number}"
            ),
            parent=self.win,
        )

        self.win.destroy()
        self.on_done()

class InvoiceViewer:
    def __init__(self, parent, invoice):
        win = tk.Toplevel(parent)
        win.title(f"Invoice - {invoice.invoice_id}")
        win.geometry("520x560")
        win.configure(bg=COLORS["bg"])
        win.transient(parent)

        hdr = tk.Frame(win, bg=COLORS["primary"], height=55)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="Invoice / Bill", font=FONTS["heading"], bg=COLORS["primary"], fg="white").pack(expand=True)

        text = tk.Text(win, font=FONTS["mono"], bg="#FAFAFA", relief="flat", padx=16, pady=16)
        text.pack(fill="both", expand=True)
        text.insert("1.0", invoice.generate_invoice_text())
        text.config(state="disabled")

        def save():
            filename = filedialog.asksaveasfilename(
                parent=win,
                title="Export Invoice",
                initialfile=f"invoice_{invoice.order.order_id}.pdf",
                defaultextension=".pdf",
                filetypes=[
                    ("PDF files", "*.pdf"),
                    ("PNG image", "*.png"),
                ],
            )
            if not filename:
                return
            try:
                export_invoice_document(invoice, filename)
            except Exception as exc:
                messagebox.showerror("Export Failed", str(exc), parent=win)
                return
            messagebox.showinfo("Saved", f"Invoice saved as {filename}", parent=win)

        tk.Button(
            win,
            text="Export PDF / PNG",
            font=FONTS["button"],
            bg=COLORS["primary"],
            fg="white",
            relief="flat",
            padx=14,
            pady=6,
            cursor="hand2",
            command=save,
        ).pack(pady=10)
