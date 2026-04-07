import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from data.store import Session
from gui.payment_workflows import PaymentVerificationDialog, RefundProcessingDialog
from gui.theme import COLORS, FONTS
from models.coupon import Coupon
from models.smartphone import Smartphone
from utils.document_export import export_sales_report_document


def format_inr(amount):
    return f"Rs {amount:,.0f}"


class AdminPortal:
    STATUS_BG = {
        "Pending": "#FEF3C7",
        "Processing": "#DBEAFE",
        "Shipped": "#E0F2FE",
        "Delivered": "#DCFCE7",
        "Cancelled": "#FEE2E2",
    }

    def __init__(self, admin, store):
        self.admin = admin
        self.store = store
        self._current_view = self._show_products

        self.root = tk.Toplevel()
        self.root.title(f"SmartShop Admin - {admin.name}")
        self.root.geometry("1180x720")
        self.root.configure(bg=COLORS["bg"])
        self.root.protocol("WM_DELETE_WINDOW", self.root.destroy)
        self._center()
        self._build_shell()
        self._show_products()

    def _center(self):
        w, h = 1180, 720
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
        top = tk.Frame(self.root, bg=COLORS["admin_top"], height=56)
        top.pack(fill="x")
        top.pack_propagate(False)
        tk.Label(top, text="SmartShop Admin Panel", font=("Segoe UI", 13, "bold"), bg=COLORS["admin_top"], fg="white").pack(side="left", padx=18)

        right = tk.Frame(top, bg=COLORS["admin_top"])
        right.pack(side="right", padx=18)
        tk.Button(right, text="Refresh", font=FONTS["small"], bg="#334155", fg="white", relief="flat", padx=10, pady=4, cursor="hand2", command=self._refresh_view).pack(side="right")
        tk.Label(right, text=f"{self.admin.name} | {self.admin.role.title()}", font=FONTS["body"], bg=COLORS["admin_top"], fg="#94A3B8").pack(side="right", padx=(0, 12))

        sidebar = tk.Frame(self.root, bg=COLORS["admin_sidebar"], width=200)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)
        tk.Label(sidebar, text="ADMIN MENU", font=FONTS["small"], bg=COLORS["admin_sidebar"], fg="#64748B").pack(pady=(22, 8), padx=14, anchor="w")

        nav = [
            ("Products", self._show_products),
            ("Customers", self._show_customers),
            ("Coupons", self._show_coupons),
            ("Sales Report", self._show_reports),
        ]
        for text, cmd in nav:
            tk.Button(
                sidebar,
                text=text,
                font=FONTS["body"],
                bg=COLORS["admin_sidebar"],
                fg="white",
                relief="flat",
                anchor="w",
                padx=14,
                pady=12,
                cursor="hand2",
                activebackground=COLORS["admin_hover"],
                activeforeground="white",
                command=cmd,
            ).pack(fill="x")

        tk.Label(sidebar, text="ORDERS", font=FONTS["small"], bg=COLORS["admin_sidebar"], fg="#64748B").pack(pady=(16, 6), padx=14, anchor="w")
        tk.Button(
            sidebar,
            text="Manage Orders",
            font=FONTS["body"],
            bg=COLORS["admin_sidebar"],
            fg="white",
            relief="flat",
            anchor="w",
            padx=28,
            pady=10,
            cursor="hand2",
            activebackground=COLORS["admin_hover"],
            activeforeground="white",
            command=self._show_manage_orders,
        ).pack(fill="x")
        tk.Button(
            sidebar,
            text="View Orders",
            font=FONTS["body"],
            bg=COLORS["admin_sidebar"],
            fg="white",
            relief="flat",
            anchor="w",
            padx=28,
            pady=10,
            cursor="hand2",
            activebackground=COLORS["admin_hover"],
            activeforeground="white",
            command=self._show_view_orders,
        ).pack(fill="x")

        tk.Button(sidebar, text="Logout", bg=COLORS["error"], fg="white", font=("Arial", 11, "bold"), cursor="hand2", command=self.logout).pack(side="bottom", pady=20, fill="x")

        self.content = tk.Frame(self.root, bg=COLORS["bg"])
        self.content.pack(side="right", fill="both", expand=True)

    def _clear(self):
        for widget in self.content.winfo_children():
            widget.destroy()
        for attr in (
            "_order_tree",
            "_order_view_tree",
            "_order_preview",
            "_order_customer_combo",
            "_order_status_combo",
            "_order_payment_combo",
            "_order_verification_combo",
            "_order_stat_cards",
            "_status_var",
            "_order_notebook",
            "_manage_orders_tab",
            "_view_orders_tab",
        ):
            setattr(self, attr, None)

    def _refresh_view(self):
        self.store.reload()
        fresh = self.store.get_user_by_id(self.admin.user_id)
        if fresh:
            self.admin = fresh
            Session.login(self.admin)
        (self._current_view or self._show_products)()

    @staticmethod
    def _make_tree(parent, cols, widths, height=16):
        style = ttk.Style()
        style.configure(
            "Adm.Treeview",
            rowheight=27,
            font=FONTS["body"],
            background=COLORS["card"],
            fieldbackground=COLORS["card"],
        )
        style.configure(
            "Adm.Treeview.Heading",
            font=FONTS["subheading"],
            background=COLORS["table_header"],
        )

        wrap = tk.Frame(parent, bg=COLORS["bg"])
        tree = ttk.Treeview(wrap, columns=cols, show="headings", style="Adm.Treeview", height=height)
        for col, width in zip(cols, widths):
            tree.heading(col, text=col)
            tree.column(col, width=width, anchor="center")
        scrollbar = ttk.Scrollbar(wrap, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        return wrap, tree


    def _selected_order_from_tree(self, tree_attr, show_message=True):
        tree = getattr(self, tree_attr, None)
        selection = tree.selection() if tree and tree.winfo_exists() else ()
        if not selection:
            if show_message:
                messagebox.showwarning("Select", "Please select an order.", parent=self.root)
            return None
        return self.store.get_order_by_id(selection[0])

    def _selected_manage_order(self, show_message=True):
        return self._selected_order_from_tree("_order_tree", show_message=show_message)

    def _selected_view_order(self, show_message=True):
        return self._selected_order_from_tree("_order_view_tree", show_message=show_message)

    def _selected_order(self, show_message=True):
        order = self._selected_manage_order(show_message=False)
        if order:
            return order
        order = self._selected_view_order(show_message=False)
        if order:
            return order
        if show_message:
            messagebox.showwarning("Select", "Please select an order.", parent=self.root)
        return None

    def _display_total_for_order(self, order):
        invoice = next((entry for entry in self.store.invoices if entry.order.order_id == order.order_id), None)
        return invoice.total_amount if invoice else order.total_amount

    def _payment_for_order(self, order):
        return self.store.get_payment_for_order(order.order_id)

    def _shipment_for_order(self, order):
        return next((entry for entry in self.store.shipments if entry.order.order_id == order.order_id), None)

    @staticmethod
    def _order_item_summary(order):
        return ", ".join(
            f"{item.smartphone.brand} {item.smartphone.model} x{item.quantity}"
            for item in order.order_items
        )

    def _populate_order_tree(self, tree, orders, include_items=False):
        tree.delete(*tree.get_children())
        for status, color in self.STATUS_BG.items():
            tree.tag_configure(status, background=color)

        for order in reversed(list(orders)):
            payment = self._payment_for_order(order)
            base_values = [
                f"#{order.order_id}",
                order.customer.name,
                order.order_date,
                format_inr(self._display_total_for_order(order)),
                order.order_status,
                payment.payment_status if payment else "-",
                payment.verification_label() if payment else "-",
                payment.refund_label() if payment else "-",
            ]
            if include_items:
                values = (
                    base_values[0],
                    base_values[1],
                    self._order_item_summary(order),
                    base_values[4],
                    base_values[5],
                    base_values[6],
                    base_values[2],
                    base_values[3],
                )
            else:
                values = tuple(base_values)
            tree.insert("", "end", iid=order.order_id, values=values, tags=(order.order_status,))

    def _order_stats(self):
        orders = self.store.orders
        refunds_pending = sum(
            1
            for order in orders
            if (self._payment_for_order(order) and self._payment_for_order(order).refund_status == "Pending")
        )
        return {
            "total": len(orders),
            "pending": sum(1 for order in orders if order.order_status in {"Pending", "Processing"}),
            "delivered": sum(1 for order in orders if order.order_status == "Delivered"),
            "refunds_pending": refunds_pending,
        }

    def _show_products(self):
        self._current_view = self._show_products
        self._clear()

        frame = tk.Frame(self.content, bg=COLORS["bg"])
        frame.pack(fill="both", expand=True, padx=20, pady=14)

        top = tk.Frame(frame, bg=COLORS["bg"])
        top.pack(fill="x", pady=(0, 10))
        tk.Label(top, text="Product Management", font=FONTS["heading"], bg=COLORS["bg"], fg=COLORS["text"]).pack(side="left")
        tk.Button(top, text="Add Product", font=FONTS["button"], bg=COLORS["success"], fg="white", relief="flat", padx=14, pady=5, cursor="hand2", command=self._add_product_dialog).pack(side="right")

        ribbon = tk.Frame(frame, bg=COLORS["bg"])
        ribbon.pack(fill="x", pady=(0, 8))
        stats = [
            ("Total Products", str(len(self.store.smartphones)), COLORS["primary"]),
            ("Total Stock", str(sum(phone.stock_quantity for phone in self.store.smartphones)), COLORS["success"]),
            ("Out of Stock", str(sum(1 for phone in self.store.smartphones if phone.stock_quantity == 0)), COLORS["error"]),
        ]
        for title, value, color in stats:
            card = tk.Frame(ribbon, bg=COLORS["card"], relief="solid", bd=1, padx=16, pady=8)
            card.pack(side="left", padx=(0, 10))
            tk.Label(card, text=value, font=("Segoe UI", 16, "bold"), bg=COLORS["card"], fg=color).pack()
            tk.Label(card, text=title, font=FONTS["small"], bg=COLORS["card"], fg=COLORS["subtext"]).pack()

        cols = ("ID", "Brand", "Model", "Price", "RAM", "Storage", "OS", "Stock")
        widths = [80, 100, 190, 90, 70, 90, 110, 70]
        wrap, self._prod_tree = self._make_tree(frame, cols, widths, height=16)
        wrap.pack(fill="both", expand=True)
        self._prod_tree.tag_configure("normal", background=COLORS["table_row"])
        self._prod_tree.tag_configure("alt", background=COLORS["table_alt"])
        self._prod_tree.tag_configure("low", background="#FEF3C7")
        self._load_products()

        bar = tk.Frame(frame, bg=COLORS["bg"])
        bar.pack(fill="x", pady=(10, 0))
        tk.Button(bar, text="Edit Selected", font=FONTS["button"], bg=COLORS["warning"], fg="white", relief="flat", padx=12, pady=5, cursor="hand2", command=self._edit_product_dialog).pack(side="left", padx=(0, 6))
        tk.Button(bar, text="Delete Selected", font=FONTS["button"], bg=COLORS["error"], fg="white", relief="flat", padx=12, pady=5, cursor="hand2", command=self._delete_product).pack(side="left")

    def _load_products(self):
        self._prod_tree.delete(*self._prod_tree.get_children())
        for idx, phone in enumerate(self.store.smartphones):
            tag = "low" if phone.stock_quantity <= 5 else ("normal" if idx % 2 == 0 else "alt")
            self._prod_tree.insert(
                "",
                "end",
                iid=phone.phone_id,
                values=(
                    phone.phone_id[:6],
                    phone.brand,
                    phone.model,
                    format_inr(phone.price),
                    phone.ram,
                    phone.storage,
                    phone.operating_system,
                    phone.stock_quantity,
                ),
                tags=(tag,),
            )

    def _selected_product(self):
        selection = self._prod_tree.selection() if hasattr(self, "_prod_tree") else ()
        if not selection:
            messagebox.showwarning("Select", "Please select a product.", parent=self.root)
            return None
        return self.store.get_phone_by_id(selection[0])

    def _add_product_dialog(self):
        ProductFormDialog(self.root, self.store, self.admin, self._load_products)

    def _edit_product_dialog(self):
        phone = self._selected_product()
        if phone:
            ProductFormDialog(self.root, self.store, self.admin, self._load_products, phone=phone)

    def _delete_product(self):
        phone = self._selected_product()
        if not phone:
            return
        if not messagebox.askyesno("Delete Product", f"Delete {phone.brand} {phone.model}?", parent=self.root):
            return
        try:
            self.store.delete_smartphone(phone.phone_id)
            self._load_products()
        except Exception as exc:
            messagebox.showerror("Delete Failed", str(exc), parent=self.root)



    def _build_order_workspace(self, title):
        frame = tk.Frame(self.content, bg=COLORS["bg"])
        frame.pack(fill="both", expand=True, padx=20, pady=14)

        tk.Label(frame, text=title, font=FONTS["heading"], bg=COLORS["bg"], fg=COLORS["text"]).pack(anchor="w", pady=(0, 10))

        stats_bar = tk.Frame(frame, bg=COLORS["bg"])
        stats_bar.pack(fill="x", pady=(0, 10))
        self._order_stat_cards = {}
        for key, stat_title, color in [
            ("total", "Total Orders", COLORS["primary"]),
            ("pending", "Pending Action", COLORS["warning"]),
            ("delivered", "Delivered", COLORS["success"]),
            ("refunds_pending", "Refund Requests", "#0F766E"),
        ]:
            card = tk.Frame(stats_bar, bg=COLORS["card"], relief="solid", bd=1, padx=16, pady=8)
            card.pack(side="left", padx=(0, 10))
            value_lbl = tk.Label(card, text="0", font=("Segoe UI", 16, "bold"), bg=COLORS["card"], fg=color)
            value_lbl.pack()
            tk.Label(card, text=stat_title, font=FONTS["small"], bg=COLORS["card"], fg=COLORS["subtext"]).pack()
            self._order_stat_cards[key] = value_lbl

        workspace = tk.Frame(frame, bg=COLORS["bg"])
        workspace.pack(fill="both", expand=True)
        return workspace

    def _show_orders(self):
        self._show_manage_orders()

    def _show_manage_orders(self):
        self._current_view = self._show_manage_orders
        self._clear()
        workspace = self._build_order_workspace("Manage Orders")
        self._build_manage_orders_tab(workspace)
        self._refresh_order_views()

    def _show_view_orders(self):
        self._current_view = self._show_view_orders
        self._clear()
        workspace = self._build_order_workspace("View Orders")
        self._build_view_orders_tab(workspace)
        self._refresh_order_views()

    def _build_manage_orders_tab(self, parent):
        cols = ("Order ID", "Customer", "Date", "Total", "Status", "Payment", "Verified", "Refund")
        widths = [90, 170, 95, 90, 110, 130, 100, 100]
        wrap, self._order_tree = self._make_tree(parent, cols, widths, height=15)
        wrap.pack(fill="both", expand=True, padx=8, pady=(10, 0))
        self._order_tree.bind("<<TreeviewSelect>>", self._on_manage_order_select)

        bar = tk.Frame(parent, bg=COLORS["bg"])
        bar.pack(fill="x", padx=8, pady=(10, 10))
        tk.Label(bar, text="Update Status:", font=FONTS["body"], bg=COLORS["bg"], fg=COLORS["text"]).pack(side="left", padx=(0, 6))

        from models.order import Order
        self._status_var = tk.StringVar(value="Processing")
        ttk.Combobox(bar, textvariable=self._status_var, values=Order.STATUSES, state="readonly", width=14).pack(side="left", padx=(0, 6))
        tk.Button(bar, text="Update", font=FONTS["button"], bg=COLORS["primary"], fg="white", relief="flat", padx=10, pady=5, cursor="hand2", command=self._update_status).pack(side="left", padx=(0, 12))
        tk.Button(bar, text="Verify Payment", font=FONTS["button"], bg="#0F766E", fg="white", relief="flat", padx=10, pady=5, cursor="hand2", command=self._verify_payment).pack(side="left", padx=(0, 6))
        tk.Button(bar, text="Process Refund", font=FONTS["button"], bg=COLORS["warning"], fg="white", relief="flat", padx=10, pady=5, cursor="hand2", command=self._process_refund).pack(side="left", padx=(0, 6))
        tk.Button(bar, text="View Details", font=FONTS["button"], bg="#64748B", fg="white", relief="flat", padx=10, pady=5, cursor="hand2", command=self._view_order_details).pack(side="left", padx=(0, 6))
        tk.Button(bar, text="View Invoice", font=FONTS["button"], bg=COLORS["primary"], fg="white", relief="flat", padx=10, pady=5, cursor="hand2", command=self._view_invoice).pack(side="left")

    def _build_view_orders_tab(self, parent):
        self._order_search_var = tk.StringVar()
        self._order_customer_filter = tk.StringVar(value="All Customers")
        self._order_category_filter = tk.StringVar(value="All Categories")
        self._order_status_filter = tk.StringVar(value="All Statuses")
        self._order_payment_filter = tk.StringVar(value="All Payments")
        self._order_verification_filter = tk.StringVar(value="All Verification")
        self._order_results_var = tk.StringVar(value="")

        for var in (
            self._order_search_var,
            self._order_customer_filter,
            self._order_category_filter,
            self._order_status_filter,
            self._order_payment_filter,
            self._order_verification_filter,
        ):
            var.trace_add("write", lambda *_: self._refresh_order_browser())

        filters = tk.Frame(parent, bg=COLORS["card"], relief="solid", bd=1, padx=14, pady=12)
        filters.pack(fill="x", padx=8, pady=(10, 10))

        row1 = tk.Frame(filters, bg=COLORS["card"])
        row1.pack(fill="x", pady=(0, 8))
        row2 = tk.Frame(filters, bg=COLORS["card"])
        row2.pack(fill="x")

        tk.Label(row1, text="Search", font=FONTS["small"], bg=COLORS["card"], fg=COLORS["text"]).pack(side="left")
        tk.Entry(row1, textvariable=self._order_search_var, font=FONTS["body"], relief="solid", bd=1, width=28).pack(side="left", padx=(8, 16), ipady=4)

        tk.Label(row1, text="Customer", font=FONTS["small"], bg=COLORS["card"], fg=COLORS["text"]).pack(side="left")
        self._order_customer_combo = ttk.Combobox(row1, textvariable=self._order_customer_filter, state="readonly", width=22)
        self._order_customer_combo.pack(side="left", padx=(8, 16))

        tk.Label(row1, text="Category", font=FONTS["small"], bg=COLORS["card"], fg=COLORS["text"]).pack(side="left")
        ttk.Combobox(
            row1,
            textvariable=self._order_category_filter,
            values=[
                "All Categories",
                "Pending Action",
                "In Transit",
                "Completed",
                "Cancelled",
                "Payment Pending",
                "Refund Pending",
                "Refund Completed",
            ],
            state="readonly",
            width=18,
        ).pack(side="left", padx=(8, 0))

        tk.Label(row2, text="Status", font=FONTS["small"], bg=COLORS["card"], fg=COLORS["text"]).pack(side="left")
        self._order_status_combo = ttk.Combobox(row2, textvariable=self._order_status_filter, state="readonly", width=18)
        self._order_status_combo.pack(side="left", padx=(8, 16))

        tk.Label(row2, text="Payment", font=FONTS["small"], bg=COLORS["card"], fg=COLORS["text"]).pack(side="left")
        self._order_payment_combo = ttk.Combobox(row2, textvariable=self._order_payment_filter, state="readonly", width=18)
        self._order_payment_combo.pack(side="left", padx=(8, 16))

        tk.Label(row2, text="Verification", font=FONTS["small"], bg=COLORS["card"], fg=COLORS["text"]).pack(side="left")
        self._order_verification_combo = ttk.Combobox(row2, textvariable=self._order_verification_filter, state="readonly", width=18)
        self._order_verification_combo.pack(side="left", padx=(8, 16))

        tk.Button(row2, text="Reset Filters", font=FONTS["button"], bg="#64748B", fg="white", relief="flat", padx=10, pady=4, cursor="hand2", command=self._reset_order_filters).pack(side="right")
        tk.Label(filters, textvariable=self._order_results_var, font=FONTS["small"], bg=COLORS["card"], fg=COLORS["subtext"]).pack(anchor="w", pady=(8, 0))

        body = tk.Frame(parent, bg=COLORS["bg"])
        body.pack(fill="both", expand=True, padx=8, pady=(0, 10))

        left = tk.Frame(body, bg=COLORS["bg"])
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))
        right = tk.Frame(body, bg=COLORS["card"], relief="solid", bd=1, padx=14, pady=12, width=300)
        right.pack(side="right", fill="both")
        right.pack_propagate(False)

        cols = ("Order ID", "Customer", "Items", "Status", "Payment", "Verified", "Date", "Total")
        widths = [85, 130, 240, 95, 110, 95, 95, 85]
        wrap, self._order_view_tree = self._make_tree(left, cols, widths, height=14)
        wrap.pack(fill="both", expand=True)
        self._order_view_tree.bind("<<TreeviewSelect>>", self._update_order_preview)
        self._order_view_tree.bind("<Double-1>", lambda _event: self._view_order_details(self._selected_view_order()))

        tk.Label(right, text="Order Snapshot", font=FONTS["subheading"], bg=COLORS["card"], fg=COLORS["text"]).pack(anchor="w")
        self._order_preview = tk.Text(right, font=FONTS["mono"], bg="#FAFAFA", relief="flat", height=18, wrap="word")
        self._order_preview.pack(fill="both", expand=True, pady=(10, 10))
        self._order_preview.insert("1.0", "Select an order to inspect customer, payment, shipment, and item details.")
        self._order_preview.config(state="disabled")

        actions = tk.Frame(right, bg=COLORS["card"])
        actions.pack(fill="x")
        tk.Button(actions, text="View Details", font=FONTS["button"], bg="#64748B", fg="white", relief="flat", padx=10, pady=5, cursor="hand2", command=lambda: self._view_order_details(self._selected_view_order())).pack(fill="x", pady=(0, 6))
        tk.Button(actions, text="View Invoice", font=FONTS["button"], bg=COLORS["primary"], fg="white", relief="flat", padx=10, pady=5, cursor="hand2", command=lambda: self._view_invoice(self._selected_view_order())).pack(fill="x")

    def _load_orders(self):
        if self._order_tree is not None and self._order_tree.winfo_exists():
            self._populate_order_tree(self._order_tree, self.store.orders, include_items=False)

    def _refresh_order_browser(self):
        if self._order_view_tree is None or not self._order_view_tree.winfo_exists():
            return
        orders = self._filtered_orders()
        self._populate_order_tree(self._order_view_tree, orders, include_items=True)
        self._order_results_var.set(f"Showing {len(orders)} of {len(self.store.orders)} orders")
        self._update_order_preview()

    def _refresh_order_views(self):
        stats = self._order_stats()
        for key, label in (self._order_stat_cards or {}).items():
            label.config(text=str(stats.get(key, 0)))
        self._load_orders()
        self._refresh_order_filter_choices()
        self._refresh_order_browser()

    def _refresh_order_filter_choices(self):
        if self._order_customer_combo is None or not self._order_customer_combo.winfo_exists():
            return

        customers = ["All Customers"] + sorted({order.customer.name for order in self.store.orders})
        statuses = ["All Statuses"] + list(dict.fromkeys(order.order_status for order in self.store.orders))
        payment_methods = ["All Payments"] + sorted(
            {payment.payment_method for payment in self.store.payments if getattr(payment, "payment_method", "")}
        )
        verification_values = ["All Verification"] + sorted(
            {payment.verification_label() for payment in self.store.payments if hasattr(payment, "verification_label")}
        )

        self._order_customer_combo.configure(values=customers)
        self._order_status_combo.configure(values=statuses)
        self._order_payment_combo.configure(values=payment_methods)
        self._order_verification_combo.configure(values=verification_values)

        if self._order_customer_filter.get() not in customers:
            self._order_customer_filter.set("All Customers")
        if self._order_status_filter.get() not in statuses:
            self._order_status_filter.set("All Statuses")
        if self._order_payment_filter.get() not in payment_methods:
            self._order_payment_filter.set("All Payments")
        if self._order_verification_filter.get() not in verification_values:
            self._order_verification_filter.set("All Verification")

    def _order_matches_category(self, order, payment, category):
        if category == "All Categories":
            return True
        if category == "Pending Action":
            return order.order_status in {"Pending", "Processing"}
        if category == "In Transit":
            return order.order_status == "Shipped"
        if category == "Completed":
            return order.order_status == "Delivered"
        if category == "Cancelled":
            return order.order_status == "Cancelled"
        if category == "Payment Pending":
            return not payment or payment.payment_status != "Completed"
        if category == "Refund Pending":
            return bool(payment and payment.refund_status == "Pending")
        if category == "Refund Completed":
            return bool(payment and payment.refund_status == "Completed")
        return True

    def _filtered_orders(self):
        search = self._order_search_var.get().strip().lower() if hasattr(self, "_order_search_var") else ""
        customer_filter = self._order_customer_filter.get() if hasattr(self, "_order_customer_filter") else "All Customers"
        category_filter = self._order_category_filter.get() if hasattr(self, "_order_category_filter") else "All Categories"
        status_filter = self._order_status_filter.get() if hasattr(self, "_order_status_filter") else "All Statuses"
        payment_filter = self._order_payment_filter.get() if hasattr(self, "_order_payment_filter") else "All Payments"
        verification_filter = self._order_verification_filter.get() if hasattr(self, "_order_verification_filter") else "All Verification"

        filtered = []
        for order in self.store.orders:
            payment = self._payment_for_order(order)
            searchable_parts = [
                order.order_id.lower(),
                order.customer.name.lower(),
                order.customer.email.lower(),
                order.shipping_address.lower(),
                self._order_item_summary(order).lower(),
                payment.payment_method.lower() if payment else "",
                payment.transaction_reference.lower() if payment and payment.transaction_reference else "",
            ]
            if search and not any(search in part for part in searchable_parts):
                continue
            if customer_filter != "All Customers" and order.customer.name != customer_filter:
                continue
            if not self._order_matches_category(order, payment, category_filter):
                continue
            if status_filter != "All Statuses" and order.order_status != status_filter:
                continue
            if payment_filter != "All Payments" and (not payment or payment.payment_method != payment_filter):
                continue
            if verification_filter != "All Verification" and (not payment or payment.verification_label() != verification_filter):
                continue
            filtered.append(order)
        return filtered

    def _reset_order_filters(self):
        self._order_search_var.set("")
        self._order_customer_filter.set("All Customers")
        self._order_category_filter.set("All Categories")
        self._order_status_filter.set("All Statuses")
        self._order_payment_filter.set("All Payments")
        self._order_verification_filter.set("All Verification")

    def _on_manage_order_select(self, _event=None):
        order = self._selected_manage_order(show_message=False)
        if order:
            self._status_var.set(order.order_status)

    def _update_order_preview(self, _event=None):
        if self._order_preview is None or not self._order_preview.winfo_exists():
            return

        order = self._selected_view_order(show_message=False)
        lines = ["Select an order to inspect customer, payment, shipment, and item details."]
        if order:
            payment = self._payment_for_order(order)
            shipment = self._shipment_for_order(order)
            lines = [
                f"Order #{order.order_id}",
                f"Customer: {order.customer.name}",
                f"Email: {order.customer.email}",
                f"Date: {order.order_date}",
                f"Status: {order.order_status}",
                f"Total: {format_inr(self._display_total_for_order(order))}",
                f"Shipping Address: {order.shipping_address}",
                "",
                "Payment",
                f"Method: {payment.payment_method if payment else '-'}",
                f"Status: {payment.payment_status if payment else '-'}",
                f"Verification: {payment.verification_label() if payment else '-'}",
                f"Refund: {payment.refund_label() if payment else '-'}",
                "",
                "Shipment",
                f"Courier: {shipment.courier_name if shipment else '-'}",
                f"Tracking: {shipment.tracking_number if shipment else '-'}",
                f"Shipment Status: {shipment.shipment_status if shipment else '-'}",
                "",
                "Items",
            ]
            for item in order.order_items:
                lines.append(f"- {item.smartphone.brand} {item.smartphone.model} x{item.quantity}")

        self._order_preview.config(state="normal")
        self._order_preview.delete("1.0", "end")
        self._order_preview.insert("1.0", "\n".join(lines))
        self._order_preview.config(state="disabled")

    def _update_status(self):
        order = self._selected_manage_order()
        if not order:
            return
        new_status = self._status_var.get()
        self.admin.manage_orders(order, new_status)

        shipment = next((entry for entry in self.store.shipments if entry.order.order_id == order.order_id), None)
        if shipment:
            mapping = {
                "Processing": "Processing",
                "Shipped": "Dispatched",
                "Delivered": "Delivered",
                "Cancelled": "Cancelled",
            }
            if new_status in mapping:
                shipment.update_shipment_status(mapping[new_status])
                self.store.save_shipment(shipment)

        loyalty_msg = ""
        if new_status == "Delivered" and order.award_loyalty_points():
            self.store.save_customer(order.customer)
            self.store.save_order_status(order)
            loyalty_msg = f"\nAwarded {order.loyalty_points_earned} loyalty points to {order.customer.name}."

        self.store.save_order_status(order)
        self._refresh_order_views()
        messagebox.showinfo("Updated", f"Order #{order.order_id} -> {new_status}{loyalty_msg}", parent=self.root)

    def _verify_payment(self):
        order = self._selected_manage_order()
        if not order:
            return
        payment = self.store.get_payment_for_order(order.order_id)
        if not payment:
            messagebox.showinfo("No Payment", "No payment record exists for this order.", parent=self.root)
            return
        result = PaymentVerificationDialog(self.root, payment).show()
        if result is None:
            return
        payment.verify_payment(self.admin.name, result["is_paid"], result["note"])
        self.store.save_payment(payment)
        self._refresh_order_views()
        messagebox.showinfo("Saved", "Payment verification updated.", parent=self.root)

    def _process_refund(self):
        order = self._selected_manage_order()
        if not order:
            return
        payment = self.store.get_payment_for_order(order.order_id)
        if not payment:
            messagebox.showinfo("No Payment", "No payment record exists for this order.", parent=self.root)
            return
        if payment.refund_status != "Pending":
            messagebox.showinfo(
                "No Pending Refund",
                "This order does not have a pending refund request to process.",
                parent=self.root,
            )
            return
        result = RefundProcessingDialog(self.root, payment).show()
        if result is None:
            return
        payment.refund_payment(
            self.admin.name,
            refund_reference=result["reference"],
            note=result["note"] or payment.payment_note,
        )
        self.store.save_payment(payment)
        self._refresh_order_views()
        messagebox.showinfo("Refund Completed", "The refund has been marked as completed.", parent=self.root)

    def _view_order_details(self, order=None):
        order = order or self._selected_order()
        if not order:
            return
        payment = self.store.get_payment_for_order(order.order_id)
        details = order.get_order_details()
        if payment:
            details += "\n\n" + payment.generate_receipt()
        win = tk.Toplevel(self.root)
        win.title(f"Order #{order.order_id}")
        win.geometry("520x430")
        win.configure(bg=COLORS["bg"])
        text = tk.Text(win, font=FONTS["mono"], bg="#FAFAFA", relief="flat", padx=16, pady=16)
        text.pack(fill="both", expand=True)
        text.insert("1.0", details)
        text.config(state="disabled")

    def _view_invoice(self, order=None):
        order = order or self._selected_order()
        if not order:
            return
        invoice = next((entry for entry in self.store.invoices if entry.order.order_id == order.order_id), None)
        if not invoice:
            messagebox.showinfo("No Invoice", "Invoice not found for this order.", parent=self.root)
            return
        from gui.customer_portal import InvoiceViewer
        InvoiceViewer(self.root, invoice)

    def _show_customers(self):
        self._current_view = self._show_customers
        self._clear()

        frame = tk.Frame(self.content, bg=COLORS["bg"])
        frame.pack(fill="both", expand=True, padx=20, pady=14)

        tk.Label(frame, text="Customer Management", font=FONTS["heading"], bg=COLORS["bg"], fg=COLORS["text"]).pack(anchor="w", pady=(0, 10))

        from models.user import Customer
        customers = [user for user in self.store.users if isinstance(user, Customer)]

        cols = ("Name", "Email", "Phone", "Orders", "Wishlist", "Points", "Joined", "Status")
        widths = [140, 190, 110, 60, 65, 65, 95, 90]
        wrap, self._cust_tree = self._make_tree(frame, cols, widths, height=16)
        wrap.pack(fill="both", expand=True)

        for customer in customers:
            self._cust_tree.insert(
                "",
                "end",
                iid=customer.customer_id,
                values=(
                    customer.name,
                    customer.email,
                    customer.phone_number,
                    len(customer.order_history),
                    len(customer.wishlist),
                    customer.loyalty_points,
                    customer.registration_date,
                    customer.account_status.title(),
                ),
            )

        bar = tk.Frame(frame, bg=COLORS["bg"])
        bar.pack(fill="x", pady=(10, 0))
        tk.Button(bar, text="Toggle Account Status", font=FONTS["button"], bg=COLORS["warning"], fg="white", relief="flat", padx=14, pady=6, cursor="hand2", command=self._toggle_customer_status).pack(side="left")

    def _toggle_customer_status(self):
        selection = self._cust_tree.selection() if hasattr(self, "_cust_tree") else ()
        if not selection:
            messagebox.showwarning("Select", "Please select a customer.", parent=self.root)
            return
        customer = self.store.get_user_by_id(selection[0])
        if not customer:
            return
        customer.account_status = "inactive" if customer.account_status == "active" else "active"
        self.store.save_customer(customer)
        self._show_customers()

    def _show_coupons(self):
        self._current_view = self._show_coupons
        self._clear()

        frame = tk.Frame(self.content, bg=COLORS["bg"])
        frame.pack(fill="both", expand=True, padx=20, pady=14)

        top = tk.Frame(frame, bg=COLORS["bg"])
        top.pack(fill="x", pady=(0, 10))
        tk.Label(top, text="Coupon Management", font=FONTS["heading"], bg=COLORS["bg"], fg=COLORS["text"]).pack(side="left")
        tk.Button(top, text="Add Coupon", font=FONTS["button"], bg=COLORS["success"], fg="white", relief="flat", padx=14, pady=5, cursor="hand2", command=self._add_coupon_dialog).pack(side="right")

        active_count = sum(1 for coupon in self.store.coupons if coupon.is_active)
        inactive_count = len(self.store.coupons) - active_count
        ribbon = tk.Frame(frame, bg=COLORS["bg"])
        ribbon.pack(fill="x", pady=(0, 8))
        stats = [
            ("Total Coupons", str(len(self.store.coupons)), COLORS["primary"]),
            ("Active Coupons", str(active_count), COLORS["success"]),
            ("Inactive Coupons", str(inactive_count), COLORS["warning"]),
        ]
        for title, value, color in stats:
            card = tk.Frame(ribbon, bg=COLORS["card"], relief="solid", bd=1, padx=16, pady=8)
            card.pack(side="left", padx=(0, 10))
            tk.Label(card, text=value, font=("Segoe UI", 16, "bold"), bg=COLORS["card"], fg=color).pack()
            tk.Label(card, text=title, font=FONTS["small"], bg=COLORS["card"], fg=COLORS["subtext"]).pack()

        cols = ("Code", "Discount", "Status", "Created")
        widths = [180, 120, 120, 120]
        wrap, self._coupon_tree = self._make_tree(frame, cols, widths, height=16)
        wrap.pack(fill="both", expand=True)
        self._coupon_tree.tag_configure("Active", background="#DCFCE7")
        self._coupon_tree.tag_configure("Inactive", background="#FEE2E2")
        self._load_coupons()

        bar = tk.Frame(frame, bg=COLORS["bg"])
        bar.pack(fill="x", pady=(10, 0))
        tk.Button(bar, text="Toggle Active", font=FONTS["button"], bg=COLORS["warning"], fg="white", relief="flat", padx=12, pady=5, cursor="hand2", command=self._toggle_coupon_status).pack(side="left", padx=(0, 6))
        tk.Button(bar, text="Delete Coupon", font=FONTS["button"], bg=COLORS["error"], fg="white", relief="flat", padx=12, pady=5, cursor="hand2", command=self._delete_coupon).pack(side="left")

    def _load_coupons(self):
        self._coupon_tree.delete(*self._coupon_tree.get_children())
        for coupon in self.store.coupons:
            status = coupon.status_label()
            self._coupon_tree.insert(
                "",
                "end",
                iid=coupon.coupon_id,
                values=(
                    coupon.code,
                    f"{coupon.discount_percent:g}%",
                    status,
                    coupon.created_date,
                ),
                tags=(status,),
            )

    def _selected_coupon(self):
        selection = self._coupon_tree.selection() if hasattr(self, "_coupon_tree") else ()
        if not selection:
            messagebox.showwarning("Select", "Please select a coupon.", parent=self.root)
            return None
        return self.store.get_coupon_by_id(selection[0])

    def _add_coupon_dialog(self):
        CouponFormDialog(self.root, self.store, self._show_coupons)

    def _toggle_coupon_status(self):
        coupon = self._selected_coupon()
        if not coupon:
            return
        coupon.toggle_active()
        self.store.save_coupon(coupon)
        self._show_coupons()

    def _delete_coupon(self):
        coupon = self._selected_coupon()
        if not coupon:
            return
        if not messagebox.askyesno("Delete Coupon", f"Delete coupon {coupon.code}?", parent=self.root):
            return
        self.store.delete_coupon(coupon.coupon_id)
        self._show_coupons()

    def _show_reports(self):
        self._current_view = self._show_reports
        self._clear()

        frame = tk.Frame(self.content, bg=COLORS["bg"])
        frame.pack(fill="both", expand=True, padx=20, pady=14)

        tk.Label(frame, text="Sales Report", font=FONTS["heading"], bg=COLORS["bg"], fg=COLORS["text"]).pack(anchor="w", pady=(0, 14))

        try:
            report = self.admin.generate_sales_report(self.store)
        except Exception as exc:
            messagebox.showerror(
                "Report Error",
                f"Unable to generate the sales report.\n{exc}",
                parent=self.root,
            )
            return

        cards = tk.Frame(frame, bg=COLORS["bg"])
        cards.pack(fill="x", pady=(0, 16))
        card_data = [
            ("Total Orders", str(report.total_orders), COLORS["primary"]),
            ("Total Revenue", format_inr(report.total_sales), COLORS["success"]),
            ("Avg Order Value", format_inr(report.average_order_value), "#0EA5E9"),
            ("Customers", str(sum(1 for user in self.store.users if hasattr(user, "customer_id"))), COLORS["warning"]),
        ]
        for title, value, color in card_data:
            card = tk.Frame(cards, bg=COLORS["card"], relief="solid", bd=1, padx=18, pady=14)
            card.pack(side="left", expand=True, fill="x", padx=(0, 10))
            tk.Label(card, text=value, font=("Segoe UI", 18, "bold"), bg=COLORS["card"], fg=color).pack()
            tk.Label(card, text=title, font=FONTS["small"], bg=COLORS["card"], fg=COLORS["subtext"]).pack()

        analytics = tk.Frame(frame, bg=COLORS["secondary"], relief="solid", bd=1, padx=16, pady=10)
        analytics.pack(fill="x", pady=(0, 14))
        tk.Label(
            analytics,
            text=(
                f"Median Order Value: {format_inr(report.median_order_value)}    "
                f"Highest Active Order: {format_inr(report.highest_order_value)}    "
                f"Revenue Std Dev: {format_inr(report.revenue_std_dev)}"
            ),
            font=FONTS["body"],
            bg=COLORS["secondary"],
            fg=COLORS["text"],
            anchor="w",
            justify="left",
        ).pack(anchor="w")
        tk.Label(
            analytics,
            text=report.report_note,
            font=FONTS["small"],
            bg=COLORS["secondary"],
            fg=COLORS["subtext"],
            anchor="w",
            justify="left",
        ).pack(anchor="w", pady=(4, 0))

        body = tk.Frame(frame, bg=COLORS["bg"])
        body.pack(fill="both", expand=True)
        left = tk.Frame(body, bg=COLORS["bg"])
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))
        right = tk.Frame(body, bg=COLORS["bg"])
        right.pack(side="right", fill="both", expand=True)

        tk.Label(left, text="Order Status Breakdown", font=FONTS["subheading"], bg=COLORS["bg"], fg=COLORS["text"]).pack(anchor="w", pady=(0, 6))
        status_card = tk.Frame(left, bg=COLORS["card"], relief="solid", bd=1, padx=16, pady=10)
        status_card.pack(fill="x")
        for status, count in report.get_status_breakdown().items():
            row = tk.Frame(status_card, bg=COLORS["card"])
            row.pack(fill="x", pady=3)
            tk.Label(row, text=status, font=FONTS["body"], bg=COLORS["card"], fg=COLORS["text"], width=18, anchor="w").pack(side="left")
            tk.Label(row, text=f"{count} orders", font=FONTS["subheading"], bg=COLORS["card"], fg=COLORS["primary"]).pack(side="right")

        tk.Label(right, text="Top Selling Products", font=FONTS["subheading"], bg=COLORS["bg"], fg=COLORS["text"]).pack(anchor="w", pady=(0, 6))
        best_card = tk.Frame(right, bg=COLORS["card"], relief="solid", bd=1, padx=16, pady=10)
        best_card.pack(fill="x")
        best = report.get_best_selling()
        if best:
            for name, qty in best:
                row = tk.Frame(best_card, bg=COLORS["card"])
                row.pack(fill="x", pady=3)
                tk.Label(row, text=name, font=FONTS["body"], bg=COLORS["card"], fg=COLORS["text"]).pack(side="left")
                tk.Label(row, text=f"{qty} sold", font=FONTS["subheading"], bg=COLORS["card"], fg=COLORS["success"]).pack(side="right")
        else:
            tk.Label(best_card, text="No sales data yet.", font=FONTS["body"], bg=COLORS["card"], fg=COLORS["subtext"]).pack()

        def export():
            filename = filedialog.asksaveasfilename(
                parent=self.root,
                title="Export Sales Report",
                initialfile=f"sales_report_{report.generated_date}.pdf",
                defaultextension=".pdf",
                filetypes=[
                    ("PDF files", "*.pdf"),
                    ("PNG image", "*.png"),
                ],
            )
            if not filename:
                return
            try:
                export_sales_report_document(report, filename)
            except Exception as exc:
                messagebox.showerror("Export Failed", str(exc), parent=self.root)
                return
            messagebox.showinfo("Exported", f"Report saved as {filename}", parent=self.root)

        tk.Button(frame, text="Export Report", font=FONTS["button"], bg=COLORS["primary"], fg="white", relief="flat", padx=16, pady=8, cursor="hand2", command=export).pack(anchor="w", pady=16)


class CouponFormDialog:
    def __init__(self, parent, store, on_save):
        self.store = store
        self.on_save = on_save

        self.win = tk.Toplevel(parent)
        self.win.title("Add Coupon")
        self.win.geometry("420x260")
        self.win.configure(bg=COLORS["bg"])
        self.win.resizable(False, False)
        self.win.transient(parent)
        self.win.grab_set()

        self._code = tk.StringVar()
        self._discount = tk.StringVar(value="10")
        self._build()

    def _build(self):
        hdr = tk.Frame(self.win, bg=COLORS["success"], height=58)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="Add Coupon Code", font=FONTS["heading"], bg=COLORS["success"], fg="white").pack(expand=True)

        form = tk.Frame(self.win, bg=COLORS["bg"], padx=28, pady=18)
        form.pack(fill="both", expand=True)

        tk.Label(form, text="Coupon Code", font=FONTS["small"], bg=COLORS["bg"], fg=COLORS["text"]).grid(row=0, column=0, sticky="w", pady=6, padx=(0, 10))
        tk.Entry(form, textvariable=self._code, font=FONTS["body"], relief="solid", bd=1, width=26).grid(row=0, column=1, pady=6, ipady=4)

        tk.Label(form, text="Discount %", font=FONTS["small"], bg=COLORS["bg"], fg=COLORS["text"]).grid(row=1, column=0, sticky="w", pady=6, padx=(0, 10))
        tk.Entry(form, textvariable=self._discount, font=FONTS["body"], relief="solid", bd=1, width=26).grid(row=1, column=1, pady=6, ipady=4)

        tk.Label(
            form,
            text="Example: SAVE15 gives 15% off during checkout.",
            font=FONTS["small"],
            bg=COLORS["bg"],
            fg=COLORS["subtext"],
        ).grid(row=2, column=0, columnspan=2, sticky="w", pady=(6, 0))

        tk.Button(self.win, text="Save Coupon", font=FONTS["button"], bg=COLORS["success"], fg="white", relief="flat", pady=9, cursor="hand2", command=self._save).pack(fill="x", padx=28, pady=14)

    def _save(self):
        code = self._code.get().strip().upper()
        if not code:
            messagebox.showerror("Error", "Coupon code is required.", parent=self.win)
            return
        if self.store.get_coupon_by_code(code):
            messagebox.showerror("Error", "That coupon code already exists.", parent=self.win)
            return
        try:
            discount = float(self._discount.get().strip())
        except ValueError:
            messagebox.showerror("Error", "Discount percentage must be a number.", parent=self.win)
            return
        if discount <= 0 or discount > 100:
            messagebox.showerror("Error", "Discount percentage must be between 0 and 100.", parent=self.win)
            return

        self.store.save_coupon(Coupon(code, discount, is_active=True))
        self.on_save()
        self.win.destroy()


class ProductFormDialog:
    FIELDS = [
        ("Brand", "brand"),
        ("Model", "model"),
        ("Price", "price"),
        ("Storage", "storage"),
        ("RAM", "ram"),
        ("Battery", "battery_capacity"),
        ("Camera Spec", "camera_spec"),
        ("Display Size", "display_size"),
        ("Operating System", "operating_system"),
        ("Stock Quantity", "stock_quantity"),
    ]

    def __init__(self, parent, store, admin, on_save, phone=None):
        self.store = store
        self.admin = admin
        self.on_save = on_save
        self.phone = phone

        self.win = tk.Toplevel(parent)
        self.win.title("Add Product" if not phone else "Edit Product")
        self.win.geometry("500x560")
        self.win.configure(bg=COLORS["bg"])
        self.win.resizable(False, False)
        self.win.transient(parent)
        self.win.grab_set()
        self._build()

    def _build(self):
        color = COLORS["success"] if not self.phone else COLORS["warning"]
        hdr = tk.Frame(self.win, bg=color, height=58)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        title = "Add New Smartphone" if not self.phone else f"Edit - {self.phone.brand} {self.phone.model}"
        tk.Label(hdr, text=title, font=FONTS["heading"], bg=color, fg="white").pack(expand=True)

        form = tk.Frame(self.win, bg=COLORS["bg"], padx=28, pady=12)
        form.pack(fill="both", expand=True)

        self._vars = {}
        for idx, (label, attr) in enumerate(self.FIELDS):
            tk.Label(form, text=label, font=FONTS["small"], bg=COLORS["bg"], fg=COLORS["text"], anchor="w").grid(row=idx, column=0, sticky="w", pady=4, padx=(0, 10))
            var = tk.StringVar(value=str(getattr(self.phone, attr, "")) if self.phone else "")
            tk.Entry(form, textvariable=var, font=FONTS["body"], relief="solid", bd=1, width=30).grid(row=idx, column=1, pady=4, ipady=4)
            self._vars[attr] = var

        tk.Button(self.win, text="Save Product", font=FONTS["button"], bg=color, fg="white", relief="flat", pady=9, cursor="hand2", command=self._save).pack(fill="x", padx=28, pady=12)

    def _save(self):
        try:
            data = {key: value.get().strip() for key, value in self._vars.items()}
            if not all(data.values()):
                messagebox.showerror("Error", "All fields are required.", parent=self.win)
                return

            if self.phone:
                self.phone.brand = data["brand"]
                self.phone.model = data["model"]
                self.phone.price = float(data["price"])
                self.phone.storage = data["storage"]
                self.phone.ram = data["ram"]
                self.phone.battery_capacity = int(data["battery_capacity"])
                self.phone.camera_spec = data["camera_spec"]
                self.phone.display_size = float(data["display_size"])
                self.phone.operating_system = data["operating_system"]
                self.phone.stock_quantity = int(data["stock_quantity"])
                self.store.save_smartphone(self.phone)
            else:
                phone = Smartphone(
                    data["brand"],
                    data["model"],
                    float(data["price"]),
                    data["storage"],
                    data["ram"],
                    int(data["battery_capacity"]),
                    data["camera_spec"],
                    float(data["display_size"]),
                    data["operating_system"],
                    int(data["stock_quantity"]),
                )
                self.admin.add_product(phone, self.store)

            self.on_save()
            messagebox.showinfo("Saved", "Product saved successfully.", parent=self.win)
            self.win.destroy()
        except ValueError as exc:
            messagebox.showerror("Invalid Input", f"Please check numeric fields.\n{exc}", parent=self.win)
