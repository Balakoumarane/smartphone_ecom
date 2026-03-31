import tkinter as tk
from tkinter import ttk, messagebox
from gui.theme import COLORS, FONTS
from models.payment import Payment
from models.invoice import Invoice
from models.shipment import Shipment
from data.store import Session
from gui.home import HomeWindow
from tkinter import messagebox


# ═══════════════════════════════════════════════════════════════════════════════
class CustomerPortal:
    def __init__(self, customer, store):
        self.customer = customer
        self.store    = store

        self.root = tk.Toplevel()
        self.root.title(f"SmartShop  —  Welcome, {customer.name}")
        self.root.geometry("1120x680")
        self.root.configure(bg=COLORS["bg"])
        self.root.protocol("WM_DELETE_WINDOW", self.root.destroy)
        self._center()
        self._build_shell()
        self._show_browse()

    # ── Layout ────────────────────────────────────────────────────────────────
    def _center(self):
        w, h = 1120, 680
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        self.root.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}")

    def logout(self):
        confirm = messagebox.askyesno("Logout", "Are you sure?")
        if not confirm:
            return

        # 1. Clear session
        Session.logout()

        # Save reference BEFORE destroying
        win = self.win if hasattr(self, "win") else self.root

        # Schedule home window
        win.after(100, HomeWindow)

        # Destroy current window
        win.destroy()
    

    def _build_shell(self):
        # Top bar
        topbar = tk.Frame(self.root, bg=COLORS["sidebar"], height=52)
        topbar.pack(fill="x")
        topbar.pack_propagate(False)
        tk.Label(topbar, text="📱  SmartShop",
                 font=("Segoe UI", 13, "bold"),
                 bg=COLORS["sidebar"], fg="white").pack(side="left", padx=18)
        self._points_lbl = tk.Label(
            topbar,
            text=f"👤  {self.customer.name}   •   ⭐ {self.customer.loyalty_points} pts",
            font=FONTS["body"], bg=COLORS["sidebar"], fg="#BFDBFE")
        self._points_lbl.pack(side="right", padx=18)

        # Sidebar
        sidebar = tk.Frame(self.root, bg="#1E3A5F", width=175)
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

        tk.Label(sidebar, text="MENU", font=FONTS["small"],
                 bg="#1E3A5F", fg="#94A3B8").pack(pady=(20, 4), padx=14, anchor="w")

        self._nav_btns = []
        nav = [
            ("🔍  Browse",    self._show_browse),
            ("🛒  My Cart",   self._show_cart),
            ("📦  My Orders", self._show_orders),
            ("👤  Profile",   self._show_profile),
        ]
        for text, cmd in nav:
            btn = tk.Button(sidebar, text=text, font=FONTS["body"],
                            bg="#1E3A5F", fg="white", relief="flat",
                            anchor="w", padx=14, pady=10, cursor="hand2",
                            activebackground=COLORS["primary"],
                            activeforeground="white",
                            command=cmd)
            btn.pack(fill="x")
            self._nav_btns.append((btn, cmd))

        # Content area
        self.content = tk.Frame(self.root, bg=COLORS["bg"])
        self.content.pack(side="right", fill="both", expand=True)

    def _clear(self):
        for w in self.content.winfo_children():
            w.destroy()

    # ── Helper: styled Treeview ───────────────────────────────────────────────
    @staticmethod
    def _make_tree(parent, cols, widths, height=15, **kw):
        style = ttk.Style()
        style.configure("SS.Treeview",
                        rowheight=28, font=FONTS["body"],
                        background=COLORS["card"],
                        fieldbackground=COLORS["card"])
        style.configure("SS.Treeview.Heading",
                        font=FONTS["subheading"],
                        background=COLORS["table_header"])
        style.map("SS.Treeview",
                  background=[("selected", COLORS["secondary"])],
                  foreground=[("selected", COLORS["text"])])

        wrap = tk.Frame(parent, bg=COLORS["bg"])
        tree = ttk.Treeview(wrap, columns=cols, show="headings",
                            style="SS.Treeview", height=height, **kw)
        for col, w in zip(cols, widths):
            tree.heading(col, text=col)
            tree.column(col, width=w, anchor="center")
        sb = ttk.Scrollbar(wrap, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=sb.set)
        tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        return wrap, tree

    # ──────────────────────────────────────────────────────────────────────────
    #  BROWSE PRODUCTS
    # ──────────────────────────────────────────────────────────────────────────
    def _show_browse(self):
        self._clear()
        frame = tk.Frame(self.content, bg=COLORS["bg"])
        frame.pack(fill="both", expand=True, padx=20, pady=14)

        # Title row + search
        top = tk.Frame(frame, bg=COLORS["bg"])
        top.pack(fill="x", pady=(0, 10))
        tk.Label(top, text="Browse Smartphones",
                 font=FONTS["heading"], bg=COLORS["bg"],
                 fg=COLORS["text"]).pack(side="left")

        right_top = tk.Frame(top, bg=COLORS["bg"])
        right_top.pack(side="right")

        self._search_var = tk.StringVar()
        tk.Entry(right_top, textvariable=self._search_var,
                 font=FONTS["body"], relief="solid", bd=1,
                 width=18).pack(side="left", ipady=4, padx=4)

        self._cat_var = tk.StringVar(value="All Categories")
        cats = ["All Categories"] + [c.category_name for c in self.store.categories]
        ttk.Combobox(right_top, textvariable=self._cat_var,
                     values=cats, state="readonly",
                     width=14).pack(side="left", padx=4)

        tk.Button(right_top, text="Search",
                  font=FONTS["button"],
                  bg=COLORS["primary"], fg="white", relief="flat",
                  padx=10, cursor="hand2",
                  command=self._filter_products).pack(side="left", padx=4)
        tk.Button(right_top, text="Clear",
                  font=FONTS["button"],
                  bg=COLORS["border"], fg=COLORS["text"], relief="flat",
                  padx=8, cursor="hand2",
                  command=self._clear_filter).pack(side="left")

        # Product Treeview
        cols   = ("Brand", "Model", "Price", "RAM", "Storage", "OS", "Battery", "Stock")
        widths = [90, 160, 90, 65, 80, 95, 85, 60]
        tree_wrap, self._prod_tree = self._make_tree(frame, cols, widths)
        tree_wrap.pack(fill="both", expand=True)

        self._prod_tree.tag_configure("even", background=COLORS["table_alt"])
        self._prod_tree.tag_configure("odd",  background=COLORS["table_row"])
        self._prod_tree.tag_configure("out",  background="#FEE2E2", foreground="#991B1B")
        self._load_products(self.store.smartphones)

        # Action bar
        bar = tk.Frame(frame, bg=COLORS["bg"])
        bar.pack(fill="x", pady=(10, 0))
        tk.Button(bar, text="👁  Details", font=FONTS["button"],
                  bg="#64748B", fg="white", relief="flat",
                  padx=12, pady=5, cursor="hand2",
                  command=self._view_details).pack(side="left", padx=(0, 6))
        tk.Button(bar, text="🛒  Add to Cart", font=FONTS["button"],
                  bg=COLORS["primary"], fg="white", relief="flat",
                  padx=12, pady=5, cursor="hand2",
                  command=self._add_to_cart_dialog).pack(side="left")

    def _load_products(self, phones):
        self._prod_tree.delete(*self._prod_tree.get_children())
        for i, p in enumerate(phones):
            if not p.check_availability():
                tag = "out"
            else:
                tag = "even" if i % 2 == 0 else "odd"
            stock_txt = str(p.stock_quantity) if p.check_availability() else "Out of Stock"
            self._prod_tree.insert("", "end", iid=p.phone_id, values=(
                p.brand, p.model, f"₹{p.price:,.0f}",
                p.ram, p.storage, p.operating_system,
                f"{p.battery_capacity}mAh", stock_txt
            ), tags=(tag,))

    def _filter_products(self):
        kw  = self._search_var.get().strip().lower()
        cat = self._cat_var.get()
        if cat != "All Categories":
            obj = next((c for c in self.store.categories
                        if c.category_name == cat), None)
            phones = obj.get_products() if obj else self.store.smartphones
        else:
            phones = self.store.smartphones
        if kw:
            phones = [p for p in phones
                      if kw in p.brand.lower() or kw in p.model.lower()]
        self._load_products(phones)

    def _clear_filter(self):
        self._search_var.set("")
        self._cat_var.set("All Categories")
        self._load_products(self.store.smartphones)

    def _selected_phone(self):
        sel = self._prod_tree.selection()
        if not sel:
            messagebox.showwarning("Select Product",
                                   "Please select a product first.",
                                   parent=self.root)
            return None
        return next((p for p in self.store.smartphones
                     if p.phone_id == sel[0]), None)

    def _view_details(self):
        phone = self._selected_phone()
        if not phone:
            return
        win = tk.Toplevel(self.root)
        win.title(f"{phone.brand} {phone.model}")
        win.geometry("500x430")
        win.configure(bg=COLORS["bg"])
        win.grab_set()

        tk.Label(win, text=f"{phone.brand} {phone.model}",
                 font=FONTS["heading"], bg=COLORS["bg"],
                 fg=COLORS["text"]).pack(pady=(22, 2))
        tk.Label(win, text=f"₹{phone.price:,.0f}",
                 font=("Segoe UI", 18, "bold"),
                 bg=COLORS["bg"], fg=COLORS["primary"]).pack()

        card = tk.Frame(win, bg=COLORS["card"], relief="solid", bd=1)
        card.pack(fill="both", expand=True, padx=22, pady=16)

        specs = [
            ("Operating System", phone.operating_system),
            ("RAM",              phone.ram),
            ("Storage",          phone.storage),
            ("Battery",          f"{phone.battery_capacity} mAh"),
            ("Camera",           phone.camera_spec),
            ("Display",          f'{phone.display_size}"'),
            ("Availability",     f"{phone.stock_quantity} units in stock"
                                 if phone.check_availability() else "Out of Stock"),
        ]
        for lbl, val in specs:
            row = tk.Frame(card, bg=COLORS["card"])
            row.pack(fill="x", padx=16, pady=5)
            tk.Label(row, text=lbl + ":", font=FONTS["subheading"],
                     bg=COLORS["card"], fg=COLORS["subtext"],
                     width=18, anchor="w").pack(side="left")
            tk.Label(row, text=val, font=FONTS["body"],
                     bg=COLORS["card"], fg=COLORS["text"]).pack(side="left")

    def _add_to_cart_dialog(self):
        phone = self._selected_phone()
        if not phone:
            return
        if not phone.check_availability():
            messagebox.showerror("Out of Stock",
                                 "This product is currently out of stock.",
                                 parent=self.root)
            return
        win = tk.Toplevel(self.root)
        win.title("Add to Cart")
        win.geometry("320x230")
        win.configure(bg=COLORS["bg"])
        win.grab_set()

        tk.Label(win, text=f"{phone.brand} {phone.model}",
                 font=FONTS["subheading"], bg=COLORS["bg"],
                 fg=COLORS["text"]).pack(pady=(22, 2))
        tk.Label(win, text=f"₹{phone.price:,.0f} each",
                 font=FONTS["body"], bg=COLORS["bg"],
                 fg=COLORS["primary"]).pack()

        tk.Label(win, text="Quantity:", font=FONTS["body"],
                 bg=COLORS["bg"], fg=COLORS["text"]).pack(pady=(18, 4))
        qty_var = tk.IntVar(value=1)
        ttk.Spinbox(win, from_=1, to=min(10, phone.stock_quantity),
                    textvariable=qty_var, width=8,
                    font=FONTS["body"]).pack()

        def confirm():
            qty = qty_var.get()
            self.customer.cart.add_item(phone, qty)
            messagebox.showinfo(
                "Added to Cart ✅",
                f"{qty}× {phone.brand} {phone.model} added to cart!",
                parent=win)
            win.destroy()

        tk.Button(win, text="Add to Cart",
                  font=FONTS["button"],
                  bg=COLORS["primary"], fg="white", relief="flat",
                  padx=18, pady=6, cursor="hand2",
                  command=confirm).pack(pady=16)

    # ──────────────────────────────────────────────────────────────────────────
    #  CART
    # ──────────────────────────────────────────────────────────────────────────
    def _show_cart(self):
        self._clear()
        frame = tk.Frame(self.content, bg=COLORS["bg"])
        frame.pack(fill="both", expand=True, padx=20, pady=14)

        tk.Label(frame, text="Shopping Cart",
                 font=FONTS["heading"], bg=COLORS["bg"],
                 fg=COLORS["text"]).pack(anchor="w", pady=(0, 10))

        cols   = ("Product", "Price", "Quantity", "Subtotal")
        widths = [280, 110, 100, 120]
        wrap, self._cart_tree = self._make_tree(frame, cols, widths, height=12)
        wrap.pack(fill="x")
        self._refresh_cart()

        # Bottom bar
        bot = tk.Frame(frame, bg=COLORS["bg"])
        bot.pack(fill="x", pady=14)

        self._total_lbl = tk.Label(
            bot,
            text=f"Total: ₹{self.customer.cart.calculate_total():,.0f}",
            font=("Segoe UI", 13, "bold"),
            bg=COLORS["bg"], fg=COLORS["primary"])
        self._total_lbl.pack(side="left")

        tk.Button(bot, text="Remove Selected",
                  font=FONTS["button"],
                  bg=COLORS["error"], fg="white", relief="flat",
                  padx=12, pady=6, cursor="hand2",
                  command=self._remove_cart_item).pack(side="right", padx=5)
        tk.Button(bot, text="Clear Cart",
                  font=FONTS["button"],
                  bg="#64748B", fg="white", relief="flat",
                  padx=12, pady=6, cursor="hand2",
                  command=self._clear_cart).pack(side="right", padx=5)
        tk.Button(bot, text="Checkout  →",
                  font=FONTS["button"],
                  bg=COLORS["success"], fg="white", relief="flat",
                  padx=12, pady=6, cursor="hand2",
                  command=self._checkout).pack(side="right", padx=5)

    def _refresh_cart(self):
        self._cart_tree.delete(*self._cart_tree.get_children())
        for item in self.customer.cart.get_cart_items():
            self._cart_tree.insert("", "end", iid=item.cart_item_id, values=(
                f"{item.smartphone.brand} {item.smartphone.model}",
                f"₹{item.price:,.0f}",
                item.quantity,
                f"₹{item.subtotal:,.0f}",
            ))

    def _remove_cart_item(self):
        sel = self._cart_tree.selection()
        if not sel:
            messagebox.showwarning("Select Item",
                                   "Please select an item to remove.",
                                   parent=self.root)
            return
        iid  = sel[0]
        item = next((i for i in self.customer.cart.items
                     if i.cart_item_id == iid), None)
        if item:
            self.customer.cart.remove_item(item.smartphone.phone_id)
            self._refresh_cart()
            self._total_lbl.config(
                text=f"Total: ₹{self.customer.cart.calculate_total():,.0f}")

    def _clear_cart(self):
        if messagebox.askyesno("Clear Cart",
                               "Remove all items from your cart?",
                               parent=self.root):
            self.customer.cart.clear_cart()
            self._refresh_cart()
            self._total_lbl.config(text="Total: ₹0")

    def _checkout(self):
        if not self.customer.cart.items:
            messagebox.showwarning("Empty Cart",
                                   "Your cart is empty!",
                                   parent=self.root)
            return
        CheckoutWindow(self.root, self.customer, self.store,
                       self._post_checkout)

    def _post_checkout(self):
        self._update_points_label()
        self._show_orders()

    def _update_points_label(self):
        self._points_lbl.config(
            text=f"👤  {self.customer.name}   •   ⭐ {self.customer.loyalty_points} pts")

    # ──────────────────────────────────────────────────────────────────────────
    #  ORDERS
    # ──────────────────────────────────────────────────────────────────────────
    def _show_orders(self):
        self._clear()
        frame = tk.Frame(self.content, bg=COLORS["bg"])
        frame.pack(fill="both", expand=True, padx=20, pady=14)

        tk.Label(frame, text="My Orders",
                 font=FONTS["heading"], bg=COLORS["bg"],
                 fg=COLORS["text"]).pack(anchor="w", pady=(0, 10))

        cols   = ("Order ID", "Date", "Items", "Total", "Status", "Payment")
        widths = [100, 100, 60, 100, 120, 120]
        wrap, self._order_tree = self._make_tree(frame, cols, widths, height=14)
        wrap.pack(fill="both", expand=True)

        self._load_orders()

        bar = tk.Frame(frame, bg=COLORS["bg"])
        bar.pack(fill="x", pady=(10, 0))

        tk.Button(bar, text="📄 View Invoice",
                  font=FONTS["button"],
                  bg=COLORS["primary"], fg="white", relief="flat",
                  padx=12, pady=6, cursor="hand2",
                  command=self._view_invoice).pack(side="left", padx=(0, 6))
        tk.Button(bar, text="🚚 Track Shipment",
                  font=FONTS["button"],
                  bg="#0EA5E9", fg="white", relief="flat",
                  padx=12, pady=6, cursor="hand2",
                  command=self._track_shipment).pack(side="left", padx=(0, 6))
        tk.Button(bar, text="❌ Cancel Order",
                  font=FONTS["button"],
                  bg=COLORS["error"], fg="white", relief="flat",
                  padx=12, pady=6, cursor="hand2",
                  command=self._cancel_order).pack(side="left")

    STATUS_COLORS = {
        "Pending":    "#FEF3C7",
        "Processing": "#DBEAFE",
        "Shipped":    "#E0F2FE",
        "Delivered":  "#DCFCE7",
        "Cancelled":  "#FEE2E2",
    }

    def _load_orders(self):
        for s, c in self.STATUS_COLORS.items():
            self._order_tree.tag_configure(s, background=c)
        self._order_tree.delete(*self._order_tree.get_children())
        for order in reversed(self.customer.order_history):
            pay = next((p for p in self.store.payments
                        if p.order.order_id == order.order_id), None)
            pay_st = pay.payment_status if pay else "—"
            self._order_tree.insert("", "end", iid=order.order_id,
                                    values=(
                                        f"#{order.order_id}",
                                        order.order_date,
                                        len(order.order_items),
                                        f"₹{order.total_amount:,.0f}",
                                        order.order_status,
                                        pay_st,
                                    ), tags=(order.order_status,))

    def _selected_order_id(self):
        sel = self._order_tree.selection()
        if not sel:
            messagebox.showwarning("Select Order",
                                   "Please select an order first.",
                                   parent=self.root)
            return None
        return sel[0]

    def _view_invoice(self):
        oid = self._selected_order_id()
        if not oid:
            return
        inv = next((i for i in self.store.invoices
                    if i.order.order_id == oid), None)
        if not inv:
            messagebox.showinfo("No Invoice",
                                "No invoice found for this order.",
                                parent=self.root)
            return
        InvoiceViewer(self.root, inv)

    def _track_shipment(self):
        oid = self._selected_order_id()
        if not oid:
            return
        shp = next((s for s in self.store.shipments
                    if s.order.order_id == oid), None)
        if not shp:
            messagebox.showinfo("No Shipment",
                                "Shipment has not been created yet.",
                                parent=self.root)
            return
        messagebox.showinfo("📦 Shipment Tracking",
                            shp.track_shipment(),
                            parent=self.root)

    def _cancel_order(self):
        oid = self._selected_order_id()
        if not oid:
            return
        order = next((o for o in self.customer.order_history
                      if o.order_id == oid), None)
        if not order:
            return
        if messagebox.askyesno("Cancel Order",
                               f"Cancel order #{oid}?",
                               parent=self.root):
            if order.cancel_order():
                self.store.save_order_status(order)
                self.store.save_stock([i.smartphone for i in order.order_items])
                messagebox.showinfo("Cancelled",
                                    "Order has been cancelled.",
                                    parent=self.root)
                self._load_orders()
            else:
                messagebox.showerror("Cannot Cancel",
                                     "Shipped or delivered orders cannot be cancelled.",
                                     parent=self.root)

    # ──────────────────────────────────────────────────────────────────────────
    #  PROFILE
    # ──────────────────────────────────────────────────────────────────────────
    def _show_profile(self):
        self._clear()
        frame = tk.Frame(self.content, bg=COLORS["bg"])
        frame.pack(fill="both", expand=True, padx=30, pady=20)

        tk.Label(frame, text="My Profile",
                 font=FONTS["heading"], bg=COLORS["bg"],
                 fg=COLORS["text"]).pack(anchor="w", pady=(0, 16))

        card = tk.Frame(frame, bg=COLORS["card"],
                        relief="solid", bd=1, padx=30, pady=20)
        card.pack(fill="x")

        read_only = ["Email", "Loyalty Points", "Member Since", "Status"]
        display   = [
            ("Name",          self.customer.name,         "name"),
            ("Email",         self.customer.email,         None),
            ("Phone",         self.customer.phone_number,  "phone"),
            ("Address",       self.customer.shipping_address or
                              self.customer.address,       "address"),
            ("Loyalty Points", str(self.customer.loyalty_points), None),
            ("Member Since",  str(self.customer.registration_date), None),
            ("Status",        self.customer.account_status.title(), None),
        ]

        self._pf_vars = {}
        for lbl, val, key in display:
            row = tk.Frame(card, bg=COLORS["card"])
            row.pack(fill="x", pady=5)
            tk.Label(row, text=lbl + ":", font=FONTS["subheading"],
                     bg=COLORS["card"], fg=COLORS["subtext"],
                     width=16, anchor="w").pack(side="left")
            var = tk.StringVar(value=val)
            if key:
                self._pf_vars[key] = var
                tk.Entry(row, textvariable=var, font=FONTS["body"],
                         relief="solid", bd=1,
                         width=38).pack(side="left")
            else:
                tk.Label(row, textvariable=var, font=FONTS["body"],
                         bg=COLORS["card"], fg=COLORS["text"]).pack(side="left")

        def save():
            self.customer.update_profile(
                self._pf_vars["name"].get(),
                self._pf_vars["phone"].get(),
                self._pf_vars["address"].get(),
            )
            self.customer.shipping_address = self._pf_vars["address"].get()
            self.store.save_customer(self.customer)
            self._update_points_label()
            messagebox.showinfo("Saved", "Profile updated successfully!",
                                parent=self.root)

        tk.Button(card, text="Save Changes",
                  font=FONTS["button"],
                  bg=COLORS["primary"], fg="white", relief="flat",
                  padx=16, pady=6, cursor="hand2",
                  command=save).pack(anchor="w", pady=(14, 0))

        # Change password section
        pw_card = tk.Frame(frame, bg=COLORS["card"],
                           relief="solid", bd=1, padx=30, pady=16)
        pw_card.pack(fill="x", pady=(16, 0))
        tk.Label(pw_card, text="Change Password",
                 font=FONTS["subheading"], bg=COLORS["card"],
                 fg=COLORS["text"]).pack(anchor="w", pady=(0, 10))

        pw_row = tk.Frame(pw_card, bg=COLORS["card"])
        pw_row.pack(fill="x")
        for ph in ["Current password", "New password"]:
            tk.Label(pw_row, text=ph, font=FONTS["small"],
                     bg=COLORS["card"], fg=COLORS["subtext"]).pack(side="left", padx=(0, 4))
        self._old_pw = tk.StringVar()
        self._new_pw = tk.StringVar()
        tk.Entry(pw_card, textvariable=self._old_pw, show="●",
                 font=FONTS["body"], relief="solid", bd=1, width=22
                 ).pack(side="left" if False else None, anchor="w", pady=2, ipady=4, fill="x")
        tk.Entry(pw_card, textvariable=self._new_pw, show="●",
                 font=FONTS["body"], relief="solid", bd=1, width=22
                 ).pack(anchor="w", pady=2, ipady=4, fill="x")

        def change_pw():
            ok = self.customer.change_password(
                self._old_pw.get(), self._new_pw.get())
            if ok:
                self.store.save_customer(self.customer)
                messagebox.showinfo("Done", "Password changed!", parent=self.root)
                self._old_pw.set(""); self._new_pw.set("")
            else:
                messagebox.showerror("Error", "Current password is incorrect.",
                                     parent=self.root)

        tk.Button(pw_card, text="Update Password",
                  font=FONTS["button"],
                  bg="#64748B", fg="white", relief="flat",
                  padx=12, pady=5, cursor="hand2",
                  command=change_pw).pack(anchor="w", pady=8)


# ═══════════════════════════════════════════════════════════════════════════════
class CheckoutWindow:
    def __init__(self, parent, customer, store, on_done):
        self.customer = customer
        self.store    = store
        self.on_done  = on_done

        self.win = tk.Toplevel(parent)
        self.win.title("Checkout")
        self.win.geometry("490x550")
        self.win.configure(bg=COLORS["bg"])
        self.win.grab_set()
        self._build()

    def _build(self):
        hdr = tk.Frame(self.win, bg=COLORS["success"], height=65)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="🛒  Checkout",
                 font=FONTS["heading"], bg=COLORS["success"],
                 fg="white").pack(expand=True)

        # Order summary
        sf = tk.Frame(self.win, bg=COLORS["secondary"],
                      relief="solid", bd=1, padx=16, pady=10)
        sf.pack(fill="x", padx=22, pady=12)
        tk.Label(sf, text="Order Summary",
                 font=FONTS["subheading"], bg=COLORS["secondary"],
                 fg=COLORS["text"]).pack(anchor="w")
        for item in self.customer.cart.items:
            tk.Label(sf,
                     text=f"  • {item.smartphone.brand} {item.smartphone.model}"
                          f"  ×{item.quantity}  —  ₹{item.subtotal:,.0f}",
                     font=FONTS["body"], bg=COLORS["secondary"],
                     fg=COLORS["text"]).pack(anchor="w")
        total = self.customer.cart.calculate_total()
        tk.Label(sf, text=f"Subtotal: ₹{total:,.0f}",
                 font=FONTS["subheading"], bg=COLORS["secondary"],
                 fg=COLORS["primary"]).pack(anchor="e", pady=(6, 0))

        # Form
        frm = tk.Frame(self.win, bg=COLORS["bg"], padx=22)
        frm.pack(fill="x")

        tk.Label(frm, text="Shipping Address *",
                 font=FONTS["subheading"], bg=COLORS["bg"],
                 fg=COLORS["text"]).pack(anchor="w", pady=(8, 2))
        self._addr = tk.StringVar(value=self.customer.shipping_address)
        tk.Entry(frm, textvariable=self._addr, font=FONTS["body"],
                 relief="solid", bd=1).pack(fill="x", ipady=6)

        tk.Label(frm, text="Payment Method *",
                 font=FONTS["subheading"], bg=COLORS["bg"],
                 fg=COLORS["text"]).pack(anchor="w", pady=(10, 2))
        self._pay_method = tk.StringVar(value="Credit Card")
        ttk.Combobox(frm, textvariable=self._pay_method,
                     values=["Credit Card", "Debit Card",
                             "UPI", "Net Banking", "Cash on Delivery"],
                     state="readonly", font=FONTS["body"]
                     ).pack(fill="x", ipady=4)

        tk.Label(frm, text="Discount Code (optional)",
                 font=FONTS["subheading"], bg=COLORS["bg"],
                 fg=COLORS["text"]).pack(anchor="w", pady=(10, 2))
        self._discount_code = tk.StringVar()
        tk.Entry(frm, textvariable=self._discount_code,
                 font=FONTS["body"], relief="solid", bd=1
                 ).pack(fill="x", ipady=5)
        tk.Label(frm, text='Try "SAVE10" for 10% off',
                 font=FONTS["small"], bg=COLORS["bg"],
                 fg=COLORS["subtext"]).pack(anchor="w")

        tk.Button(self.win, text="Place Order & Pay  →",
                  font=("Segoe UI", 11, "bold"),
                  bg=COLORS["success"], fg="white", relief="flat",
                  pady=10, cursor="hand2",
                  command=self._place).pack(fill="x", padx=22, pady=16)

    def _place(self):
        addr = self._addr.get().strip()
        if not addr:
            messagebox.showerror("Error",
                                 "Please enter a shipping address.",
                                 parent=self.win)
            return

        self.customer.shipping_address = addr
        order = self.customer.place_order(self.store)
        if not order:
            messagebox.showerror("Error", "Failed to place order.",
                                 parent=self.win)
            return

        # Payment
        payment = Payment(order, self._pay_method.get())
        payment.process_payment(order.total_amount)
        self.store.payments.append(payment)

        # Discount
        discount = 0.0
        if self._discount_code.get().strip().upper() == "SAVE10":
            discount = round(order.total_amount * 0.10, 2)

        # Invoice
        invoice = Invoice(order, discount=discount)
        self.store.invoices.append(invoice)

        # Shipment
        shp = Shipment(order)
        shp.create_shipment(order)
        self.store.shipments.append(shp)

        # Loyalty points (+1 per ₹100 spent)
        self.customer.loyalty_points += int(order.total_amount // 100)
        order.update_order_status("Processing")
        self.store.save_customer(self.customer)
        self.store.save_order_status(order)

        messagebox.showinfo(
            "Order Confirmed! 🎉",
            f"Order #{order.order_id} placed!\n\n"
            f"Total (incl. tax): ₹{invoice.total_amount:,.0f}\n"
            f"Payment: {payment.payment_status}\n"
            f"Courier: {shp.courier_name}\n"
            f"Tracking: {shp.tracking_number}\n"
            f"Est. Delivery: {shp.estimated_delivery}",
            parent=self.win)

        self.win.destroy()
        self.on_done()


# ═══════════════════════════════════════════════════════════════════════════════
class InvoiceViewer:
    def __init__(self, parent, invoice):
        win = tk.Toplevel(parent)
        win.title(f"Invoice — {invoice.invoice_id}")
        win.geometry("520x560")
        win.configure(bg=COLORS["bg"])

        hdr = tk.Frame(win, bg=COLORS["primary"], height=55)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="📄  Invoice / Bill",
                 font=FONTS["heading"], bg=COLORS["primary"],
                 fg="white").pack(expand=True)

        txt = tk.Text(win, font=FONTS["mono"], bg="#FAFAFA",
                      relief="flat", padx=16, pady=16)
        txt.pack(fill="both", expand=True)
        txt.insert("1.0", invoice.generate_invoice_text())
        txt.config(state="disabled")

        def save():
            fname = f"invoice_{invoice.order.order_id}.txt"
            with open(fname, "w") as f:
                f.write(invoice.generate_invoice_text())
            messagebox.showinfo("Saved", f"Invoice saved as  {fname}", parent=win)

        tk.Button(win, text="💾  Save as .txt",
                  font=FONTS["button"],
                  bg=COLORS["primary"], fg="white", relief="flat",
                  padx=14, pady=6, cursor="hand2",
                  command=save).pack(pady=10)
