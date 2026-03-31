import tkinter as tk
from tkinter import ttk, messagebox
from gui.theme import COLORS, FONTS
from models.smartphone import Smartphone
from tkinter import messagebox
from data.store import Session
from gui.home import HomeWindow


# ═══════════════════════════════════════════════════════════════════════════════
class AdminPortal:
    def __init__(self, admin, store):
        self.admin = admin
        self.store = store

        self.root = tk.Toplevel()
        self.root.title(f"SmartShop Admin  —  {admin.name}")
        self.root.geometry("1150x700")
        self.root.configure(bg=COLORS["bg"])
        self.root.protocol("WM_DELETE_WINDOW", self.root.destroy)
        self._center()
        self._build_shell()
        self._show_products()

    def _center(self):
        w, h = 1150, 700
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        self.root.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}")

    def logout(self):
        confirm = messagebox.askyesno("Logout", "Are you sure you want to logout?")
        if not confirm:
            return

        Session.logout()

        # Save reference BEFORE destroying
        win = self.win if hasattr(self, "win") else self.root

        # Schedule home window
        win.after(100, HomeWindow)

        # Destroy current window
        win.destroy()

    # ── Shell (top-bar + sidebar + content) ───────────────────────────────────
    def _build_shell(self):
        # Top bar
        top = tk.Frame(self.root, bg=COLORS["admin_top"], height=52)
        top.pack(fill="x")
        top.pack_propagate(False)
        tk.Label(top, text="⚙  SmartShop Admin Panel",
                 font=("Segoe UI", 13, "bold"),
                 bg=COLORS["admin_top"], fg="white").pack(side="left", padx=18)
        tk.Label(top,
                 text=f"Logged in: {self.admin.name}   |   Role: {self.admin.role.title()}",
                 font=FONTS["body"],
                 bg=COLORS["admin_top"], fg="#94A3B8").pack(side="right", padx=18)

        # Sidebar
        sidebar = tk.Frame(self.root, bg=COLORS["admin_sidebar"], width=190)
        logout_btn = tk.Button(
            sidebar,
            text="🔓 Logout",
            bg="red",
            fg="white",
            font=("Arial", 11, "bold"),
            cursor="hand2",
            command=self.logout
        )
        logout_btn.pack(side="bottom", pady=20, fill="x")
        
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        tk.Label(sidebar, text="ADMIN MENU", font=FONTS["small"],
                 bg=COLORS["admin_sidebar"], fg="#64748B"
                 ).pack(pady=(22, 6), padx=14, anchor="w")

        nav = [
            ("📦  Products",     self._show_products),
            ("📋  Orders",       self._show_orders),
            ("👥  Customers",    self._show_customers),
            ("📊  Sales Report", self._show_reports),
        ]
        for text, cmd in nav:
            tk.Button(sidebar, text=text, font=FONTS["body"],
                      bg=COLORS["admin_sidebar"], fg="white",
                      relief="flat", anchor="w",
                      padx=14, pady=12, cursor="hand2",
                      activebackground=COLORS["admin_hover"],
                      activeforeground="white",
                      command=cmd).pack(fill="x")

        # Content
        self.content = tk.Frame(self.root, bg=COLORS["bg"])
        self.content.pack(side="right", fill="both", expand=True)

    def _clear(self):
        for w in self.content.winfo_children():
            w.destroy()

    # ── Reusable styled Treeview ──────────────────────────────────────────────
    @staticmethod
    def _make_tree(parent, cols, widths, height=16):
        style = ttk.Style()
        style.configure("Adm.Treeview",
                        rowheight=27, font=FONTS["body"],
                        background=COLORS["card"],
                        fieldbackground=COLORS["card"])
        style.configure("Adm.Treeview.Heading",
                        font=FONTS["subheading"],
                        background=COLORS["table_header"])
        style.map("Adm.Treeview",
                  background=[("selected", COLORS["secondary"])],
                  foreground=[("selected", COLORS["text"])])

        wrap = tk.Frame(parent, bg=COLORS["bg"])
        tree = ttk.Treeview(wrap, columns=cols, show="headings",
                            style="Adm.Treeview", height=height)
        for col, w in zip(cols, widths):
            tree.heading(col, text=col)
            tree.column(col, width=w, anchor="center")
        sb = ttk.Scrollbar(wrap, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=sb.set)
        tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        return wrap, tree

    # ──────────────────────────────────────────────────────────────────────────
    #  PRODUCTS
    # ──────────────────────────────────────────────────────────────────────────
    def _show_products(self):
        self._clear()
        frame = tk.Frame(self.content, bg=COLORS["bg"])
        frame.pack(fill="both", expand=True, padx=20, pady=14)

        # Title + Add button
        top = tk.Frame(frame, bg=COLORS["bg"])
        top.pack(fill="x", pady=(0, 10))
        tk.Label(top, text="Product Management",
                 font=FONTS["heading"], bg=COLORS["bg"],
                 fg=COLORS["text"]).pack(side="left")
        tk.Button(top, text="＋  Add Product",
                  font=FONTS["button"],
                  bg=COLORS["success"], fg="white", relief="flat",
                  padx=14, pady=5, cursor="hand2",
                  command=self._add_product_dialog).pack(side="right")

        # Stats ribbon
        active_stock = sum(p.stock_quantity for p in self.store.smartphones)
        ribbon = tk.Frame(frame, bg=COLORS["bg"])
        ribbon.pack(fill="x", pady=(0, 8))
        for label, val, color in [
            ("Total Products", str(len(self.store.smartphones)), COLORS["primary"]),
            ("Total Stock",    str(active_stock),               COLORS["success"]),
            ("Out of Stock",   str(sum(1 for p in self.store.smartphones
                                      if p.stock_quantity == 0)), COLORS["error"]),
        ]:
            card = tk.Frame(ribbon, bg=COLORS["card"], relief="solid", bd=1,
                            padx=16, pady=8)
            card.pack(side="left", padx=(0, 10))
            tk.Label(card, text=val, font=("Segoe UI", 16, "bold"),
                     bg=COLORS["card"], fg=color).pack()
            tk.Label(card, text=label, font=FONTS["small"],
                     bg=COLORS["card"], fg=COLORS["subtext"]).pack()

        # Treeview
        cols   = ("ID", "Brand", "Model", "Price", "RAM", "Storage", "OS", "Stock")
        widths = [70, 95, 165, 80, 65, 85, 100, 65]
        wrap, self._prod_tree = self._make_tree(frame, cols, widths)
        wrap.pack(fill="both", expand=True)
        self._prod_tree.tag_configure("even", background=COLORS["table_alt"])
        self._prod_tree.tag_configure("odd",  background=COLORS["table_row"])
        self._prod_tree.tag_configure("low",  background="#FEF3C7")
        self._load_products()

        # Action bar
        bar = tk.Frame(frame, bg=COLORS["bg"])
        bar.pack(fill="x", pady=(8, 0))
        tk.Button(bar, text="✏  Edit Selected",
                  font=FONTS["button"],
                  bg=COLORS["warning"], fg="white", relief="flat",
                  padx=12, pady=5, cursor="hand2",
                  command=self._edit_product_dialog).pack(side="left", padx=(0, 6))
        tk.Button(bar, text="🗑  Delete Selected",
                  font=FONTS["button"],
                  bg=COLORS["error"], fg="white", relief="flat",
                  padx=12, pady=5, cursor="hand2",
                  command=self._delete_product).pack(side="left")

    def _load_products(self):
        self._prod_tree.delete(*self._prod_tree.get_children())
        for i, p in enumerate(self.store.smartphones):
            if p.stock_quantity == 0:
                tag = "low"
            elif p.stock_quantity <= 5:
                tag = "low"
            else:
                tag = "even" if i % 2 == 0 else "odd"
            self._prod_tree.insert("", "end", iid=p.phone_id, values=(
                p.phone_id[:6], p.brand, p.model,
                f"₹{p.price:,.0f}", p.ram, p.storage,
                p.operating_system, p.stock_quantity
            ), tags=(tag,))

    def _add_product_dialog(self):
        ProductFormDialog(self.root, self.store, self.admin,
                          self._load_products, phone=None)

    def _edit_product_dialog(self):
        sel = self._prod_tree.selection()
        if not sel:
            messagebox.showwarning("Select", "Please select a product to edit.",
                                   parent=self.root)
            return
        pid   = sel[0]
        phone = next((p for p in self.store.smartphones
                      if p.phone_id == pid), None)
        if phone:
            ProductFormDialog(self.root, self.store, self.admin,
                              self._load_products, phone=phone)

    def _delete_product(self):
        sel = self._prod_tree.selection()
        if not sel:
            messagebox.showwarning("Select", "Please select a product to delete.",
                                   parent=self.root)
            return
        pid   = sel[0]
        phone = next((p for p in self.store.smartphones
                      if p.phone_id == pid), None)
        if phone:
            if messagebox.askyesno(
                    "Delete Product",
                    f"Delete {phone.brand} {phone.model}?",
                    parent=self.root):
                self.store.delete_smartphone(pid)
                self._load_products()

    # ──────────────────────────────────────────────────────────────────────────
    #  ORDERS
    # ──────────────────────────────────────────────────────────────────────────
    STATUS_BG = {
        "Pending":    "#FEF3C7",
        "Processing": "#DBEAFE",
        "Shipped":    "#E0F2FE",
        "Delivered":  "#DCFCE7",
        "Cancelled":  "#FEE2E2",
    }

    def _show_orders(self):
        self._clear()
        frame = tk.Frame(self.content, bg=COLORS["bg"])
        frame.pack(fill="both", expand=True, padx=20, pady=14)

        tk.Label(frame, text="Order Management",
                 font=FONTS["heading"], bg=COLORS["bg"],
                 fg=COLORS["text"]).pack(anchor="w", pady=(0, 10))

        cols   = ("Order ID", "Customer", "Date", "Items", "Total", "Status")
        widths = [100, 160, 100, 60, 100, 130]
        wrap, self._order_tree = self._make_tree(frame, cols, widths)
        wrap.pack(fill="both", expand=True)
        self._load_orders()

        # Action bar
        bar = tk.Frame(frame, bg=COLORS["bg"])
        bar.pack(fill="x", pady=(10, 0))

        tk.Label(bar, text="Update Status:",
                 font=FONTS["body"], bg=COLORS["bg"],
                 fg=COLORS["text"]).pack(side="left", padx=(0, 6))

        from models.order import Order
        self._status_var = tk.StringVar(value="Processing")
        ttk.Combobox(bar, textvariable=self._status_var,
                     values=Order.STATUSES,
                     state="readonly", width=14
                     ).pack(side="left", padx=(0, 6))

        tk.Button(bar, text="Update",
                  font=FONTS["button"],
                  bg=COLORS["primary"], fg="white", relief="flat",
                  padx=10, pady=5, cursor="hand2",
                  command=self._update_status).pack(side="left", padx=(0, 14))

        tk.Button(bar, text="📄 View Details",
                  font=FONTS["button"],
                  bg="#64748B", fg="white", relief="flat",
                  padx=10, pady=5, cursor="hand2",
                  command=self._view_order_details).pack(side="left", padx=(0, 6))

        tk.Button(bar, text="📄 View Invoice",
                  font=FONTS["button"],
                  bg=COLORS["primary"], fg="white", relief="flat",
                  padx=10, pady=5, cursor="hand2",
                  command=self._view_invoice).pack(side="left")

    def _load_orders(self):
        for s, bg in self.STATUS_BG.items():
            self._order_tree.tag_configure(s, background=bg)
        self._order_tree.delete(*self._order_tree.get_children())
        for order in reversed(self.store.orders):
            self._order_tree.insert("", "end", iid=order.order_id, values=(
                f"#{order.order_id}",
                order.customer.name,
                order.order_date,
                len(order.order_items),
                f"₹{order.total_amount:,.0f}",
                order.order_status,
            ), tags=(order.order_status,))

    def _selected_order(self):
        sel = self._order_tree.selection()
        if not sel:
            messagebox.showwarning("Select", "Please select an order.",
                                   parent=self.root)
            return None
        oid = sel[0]
        return next((o for o in self.store.orders if o.order_id == oid), None)

    def _update_status(self):
        order = self._selected_order()
        if not order:
            return
        new_st = self._status_var.get()
        self.admin.manage_orders(order, new_st)

        # Sync shipment status
        shp = next((s for s in self.store.shipments
                    if s.order.order_id == order.order_id), None)
        if shp:
            mapping = {"Processing": "Processing",
                       "Shipped": "Dispatched",
                       "Delivered": "Delivered"}
            if new_st in mapping:
                shp.update_shipment_status(mapping[new_st])

        self.store.save_order_status(order)
        if shp:
            self.store.save_shipment(shp)
        self._load_orders()
        messagebox.showinfo("Updated",
                            f"Order #{order.order_id} → {new_st}",
                            parent=self.root)

    def _view_order_details(self):
        order = self._selected_order()
        if not order:
            return
        win = tk.Toplevel(self.root)
        win.title(f"Order #{order.order_id}")
        win.geometry("480x380")
        win.configure(bg=COLORS["bg"])
        txt = tk.Text(win, font=FONTS["mono"], bg="#FAFAFA",
                      relief="flat", padx=16, pady=16)
        txt.pack(fill="both", expand=True)
        txt.insert("1.0", order.get_order_details())
        txt.config(state="disabled")

    def _view_invoice(self):
        order = self._selected_order()
        if not order:
            return
        inv = next((i for i in self.store.invoices
                    if i.order.order_id == order.order_id), None)
        if not inv:
            messagebox.showinfo("No Invoice",
                                "Invoice not found for this order.",
                                parent=self.root)
            return
        from gui.customer_portal import InvoiceViewer
        InvoiceViewer(self.root, inv)

    # ──────────────────────────────────────────────────────────────────────────
    #  CUSTOMERS
    # ──────────────────────────────────────────────────────────────────────────
    def _show_customers(self):
        self._clear()
        frame = tk.Frame(self.content, bg=COLORS["bg"])
        frame.pack(fill="both", expand=True, padx=20, pady=14)

        tk.Label(frame, text="Customer Management",
                 font=FONTS["heading"], bg=COLORS["bg"],
                 fg=COLORS["text"]).pack(anchor="w", pady=(0, 10))

        from models.user import Customer
        customers = [u for u in self.store.users if isinstance(u, Customer)]

        cols   = ("Name", "Email", "Phone", "Orders", "Points", "Joined", "Status")
        widths = [150, 200, 115, 65, 65, 100, 90]
        wrap, tree = self._make_tree(frame, cols, widths, height=16)
        wrap.pack(fill="both", expand=True)

        for c in customers:
            tree.insert("", "end", iid=c.customer_id, values=(
                c.name, c.email, c.phone_number,
                len(c.order_history), c.loyalty_points,
                c.registration_date,
                c.account_status.title()
            ))
        self._cust_tree = tree

        bar = tk.Frame(frame, bg=COLORS["bg"])
        bar.pack(fill="x", pady=(10, 0))

        def toggle():
            sel = self._cust_tree.selection()
            if not sel:
                messagebox.showwarning("Select",
                                       "Please select a customer.",
                                       parent=self.root)
                return
            cid = sel[0]
            cust = next((u for u in self.store.users
                         if isinstance(u, Customer)
                         and u.customer_id == cid), None)
            if cust:
                cust.account_status = (
                    "inactive" if cust.account_status == "active" else "active")
                self.store.save_customer(cust)
                self._show_customers()

        tk.Button(bar, text="Toggle Account Status",
                  font=FONTS["button"],
                  bg=COLORS["warning"], fg="white", relief="flat",
                  padx=14, pady=6, cursor="hand2",
                  command=toggle).pack(side="left")

    # ──────────────────────────────────────────────────────────────────────────
    #  SALES REPORT
    # ──────────────────────────────────────────────────────────────────────────
    def _show_reports(self):
        self._clear()
        frame = tk.Frame(self.content, bg=COLORS["bg"])
        frame.pack(fill="both", expand=True, padx=20, pady=14)

        tk.Label(frame, text="Sales Report",
                 font=FONTS["heading"], bg=COLORS["bg"],
                 fg=COLORS["text"]).pack(anchor="w", pady=(0, 14))

        report = self.admin.generate_sales_report(self.store)

        # ── KPI Cards ─────────────────────────────────────────────────────────
        cards = tk.Frame(frame, bg=COLORS["bg"])
        cards.pack(fill="x", pady=(0, 16))

        avg = report.total_sales / max(report.total_orders, 1)
        kpis = [
            ("Total Orders",   str(report.total_orders),    COLORS["primary"]),
            ("Total Revenue",  f"₹{report.total_sales:,.0f}", COLORS["success"]),
            ("Avg Order Value", f"₹{avg:,.0f}",               "#7C3AED"),
            ("Customers",
             str(sum(1 for u in self.store.users
                     if hasattr(u, "customer_id"))),          "#0EA5E9"),
        ]
        for title, val, color in kpis:
            c = tk.Frame(cards, bg=COLORS["card"],
                         relief="solid", bd=1, padx=18, pady=14)
            c.pack(side="left", expand=True, fill="x", padx=(0, 10))
            tk.Label(c, text=val, font=("Segoe UI", 18, "bold"),
                     bg=COLORS["card"], fg=color).pack()
            tk.Label(c, text=title, font=FONTS["small"],
                     bg=COLORS["card"], fg=COLORS["subtext"]).pack()

        # ── Status breakdown ──────────────────────────────────────────────────
        two_col = tk.Frame(frame, bg=COLORS["bg"])
        two_col.pack(fill="both", expand=True)

        left_col = tk.Frame(two_col, bg=COLORS["bg"])
        left_col.pack(side="left", fill="both", expand=True, padx=(0, 10))
        right_col = tk.Frame(two_col, bg=COLORS["bg"])
        right_col.pack(side="right", fill="both", expand=True)

        # Status breakdown (left)
        tk.Label(left_col, text="Order Status Breakdown",
                 font=FONTS["subheading"], bg=COLORS["bg"],
                 fg=COLORS["text"]).pack(anchor="w", pady=(0, 6))
        bk_card = tk.Frame(left_col, bg=COLORS["card"],
                           relief="solid", bd=1, padx=16, pady=10)
        bk_card.pack(fill="x")
        status_icons = {
            "Pending": "🕐", "Processing": "⚙️", "Shipped": "🚚",
            "Delivered": "✅", "Cancelled": "❌"
        }
        for status, count in report.get_status_breakdown().items():
            icon = status_icons.get(status, "•")
            row = tk.Frame(bk_card, bg=COLORS["card"])
            row.pack(fill="x", pady=3)
            tk.Label(row, text=f"{icon}  {status}",
                     font=FONTS["body"], bg=COLORS["card"],
                     fg=COLORS["text"], width=18, anchor="w").pack(side="left")
            tk.Label(row, text=f"{count} orders",
                     font=FONTS["subheading"], bg=COLORS["card"],
                     fg=COLORS["primary"]).pack(side="right")

        # Best sellers (right)
        tk.Label(right_col, text="Top Selling Products",
                 font=FONTS["subheading"], bg=COLORS["bg"],
                 fg=COLORS["text"]).pack(anchor="w", pady=(0, 6))
        bs_card = tk.Frame(right_col, bg=COLORS["card"],
                           relief="solid", bd=1, padx=16, pady=10)
        bs_card.pack(fill="x")
        best = report.get_best_selling()
        medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
        if best:
            for i, (name, qty) in enumerate(best):
                row = tk.Frame(bs_card, bg=COLORS["card"])
                row.pack(fill="x", pady=3)
                tk.Label(row, text=f"{medals[i]}  {name}",
                         font=FONTS["body"], bg=COLORS["card"],
                         fg=COLORS["text"]).pack(side="left")
                tk.Label(row, text=f"{qty} sold",
                         font=FONTS["subheading"], bg=COLORS["card"],
                         fg=COLORS["success"]).pack(side="right")
        else:
            tk.Label(bs_card, text="No sales data yet.",
                     font=FONTS["body"], bg=COLORS["card"],
                     fg=COLORS["subtext"]).pack()

        # ── Export ────────────────────────────────────────────────────────────
        def export():
            text  = report.export_report()
            fname = f"sales_report_{report.generated_date}.txt"
            with open(fname, "w") as f:
                f.write(text)
            messagebox.showinfo("Exported",
                                f"Report saved as  {fname}",
                                parent=self.root)

        tk.Button(frame, text="📤  Export Report as .txt",
                  font=FONTS["button"],
                  bg=COLORS["primary"], fg="white", relief="flat",
                  padx=16, pady=8, cursor="hand2",
                  command=export).pack(anchor="w", pady=16)


# ═══════════════════════════════════════════════════════════════════════════════
class ProductFormDialog:
    FIELDS = [
        ("Brand",                  "brand",            False),
        ("Model",                  "model",            False),
        ("Price (₹)",              "price",            False),
        ("Storage (e.g. 256GB)",   "storage",          False),
        ("RAM (e.g. 8GB)",         "ram",              False),
        ("Battery (mAh)",          "battery_capacity", False),
        ("Camera Spec",            "camera_spec",      False),
        ("Display Size (inches)",  "display_size",     False),
        ("Operating System",       "operating_system", False),
        ("Stock Quantity",         "stock_quantity",   False),
    ]

    def __init__(self, parent, store, admin, on_save, phone=None):
        self.store   = store
        self.admin   = admin
        self.on_save = on_save
        self.phone   = phone

        self.win = tk.Toplevel(parent)
        self.win.title("Add Product" if not phone else "Edit Product")
        self.win.geometry("490x560")
        self.win.configure(bg=COLORS["bg"])
        self.win.resizable(False, False)
        self.win.grab_set()
        self._build()

    def _build(self):
        hdr_color = COLORS["success"] if not self.phone else COLORS["warning"]
        hdr = tk.Frame(self.win, bg=hdr_color, height=58)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        title = ("Add New Smartphone" if not self.phone
                 else f"Edit — {self.phone.brand} {self.phone.model}")
        tk.Label(hdr, text=title, font=FONTS["heading"],
                 bg=hdr_color, fg="white").pack(expand=True)

        frm = tk.Frame(self.win, bg=COLORS["bg"], padx=28)
        frm.pack(fill="both", expand=True, pady=10)

        self._vars = {}
        for row_i, (label, attr, _) in enumerate(self.FIELDS):
            tk.Label(frm, text=label, font=FONTS["small"],
                     bg=COLORS["bg"], fg=COLORS["text"],
                     anchor="w").grid(row=row_i, column=0,
                                      sticky="w", pady=3, padx=(0, 10))
            var = tk.StringVar()
            if self.phone:
                var.set(str(getattr(self.phone, attr, "")))
            tk.Entry(frm, textvariable=var, font=FONTS["body"],
                     relief="solid", bd=1, width=30
                     ).grid(row=row_i, column=1, pady=3, ipady=4)
            self._vars[attr] = var

        save_color = COLORS["success"] if not self.phone else COLORS["warning"]
        tk.Button(self.win,
                  text="💾  Save Product",
                  font=FONTS["button"],
                  bg=save_color, fg="white", relief="flat",
                  pady=9, cursor="hand2",
                  command=self._save).pack(fill="x", padx=28, pady=12)

    def _save(self):
        try:
            d = {k: v.get().strip() for k, v in self._vars.items()}
            if not all(d.values()):
                messagebox.showerror("Error",
                                     "All fields are required.",
                                     parent=self.win)
                return

            if self.phone:
                self.phone.brand             = d["brand"]
                self.phone.model             = d["model"]
                self.phone.price             = float(d["price"])
                self.phone.storage           = d["storage"]
                self.phone.ram               = d["ram"]
                self.phone.battery_capacity  = int(d["battery_capacity"])
                self.phone.camera_spec       = d["camera_spec"]
                self.phone.display_size      = float(d["display_size"])
                self.phone.operating_system  = d["operating_system"]
                self.phone.stock_quantity    = int(d["stock_quantity"])
                self.store.save_smartphone(self.phone)
            else:
                new_phone = Smartphone(
                    d["brand"], d["model"], float(d["price"]),
                    d["storage"], d["ram"],
                    int(d["battery_capacity"]), d["camera_spec"],
                    float(d["display_size"]), d["operating_system"],
                    int(d["stock_quantity"])
                )
                self.admin.add_product(new_phone, self.store)

            self.on_save()
            messagebox.showinfo("Saved",
                                "Product saved successfully!",
                                parent=self.win)
            self.win.destroy()

        except ValueError as exc:
            messagebox.showerror("Invalid Input",
                                 f"Please check numeric fields.\n{exc}",
                                 parent=self.win)
