import tkinter as tk
from gui.theme import COLORS, FONTS


class HomeWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("SmartShop — Smartphone E-Commerce")
        self.root.geometry("820x560")
        self.root.configure(bg=COLORS["bg"])
        self.root.resizable(False, False)
        self._center()
        self._build()

    def _center(self):
        self.root.update_idletasks()
        w, h = 820, 560
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        self.root.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}")

    def _build(self):
        # ── Left blue panel ──────────────────────────────────────────────────
        left = tk.Frame(self.root, bg=COLORS["sidebar"], width=370)
        left.pack(side="left", fill="y")
        left.pack_propagate(False)

        tk.Label(left, text="📱", font=("Segoe UI", 56),
                 bg=COLORS["sidebar"], fg="white").pack(pady=(70, 8))
        tk.Label(left, text="SmartShop",
                 font=("Segoe UI", 26, "bold"),
                 bg=COLORS["sidebar"], fg="white").pack()
        tk.Label(left, text="Smartphone E-Commerce & Billing System",
                 font=FONTS["small"], bg=COLORS["sidebar"], fg="#BFDBFE",
                 wraplength=300).pack(pady=(4, 30))

        features = [
            "✓   Browse & Compare Smartphones",
            "✓   Smart Shopping Cart",
            "✓   Secure Order Placement",
            "✓   Invoice & Tax Generation",
            "✓   Real-Time Order Tracking",
            "✓   Admin Inventory Dashboard",
        ]
        for feat in features:
            tk.Label(left, text=feat, font=FONTS["small"],
                     bg=COLORS["sidebar"], fg="#DBEAFE",
                     anchor="w").pack(fill="x", padx=50, pady=2)

        #tk.Label(left, text="Python  •  Tkinter  •  OOP",
        #         font=FONTS["small"], bg=COLORS["sidebar"],
        #         fg="#93C5FD").pack(side="bottom", pady=20)

        # ── Right white panel ────────────────────────────────────────────────
        right = tk.Frame(self.root, bg=COLORS["bg"])
        right.pack(side="right", fill="both", expand=True)

        # Spacer
        tk.Frame(right, bg=COLORS["bg"], height=60).pack()

        tk.Label(right, text="Welcome Back!",
                 font=FONTS["title"], bg=COLORS["bg"],
                 fg=COLORS["text"]).pack(pady=(0, 4))
        tk.Label(right, text="Choose how you'd like to continue",
                 font=FONTS["body"], bg=COLORS["bg"],
                 fg=COLORS["subtext"]).pack(pady=(0, 40))

        # ── Customer button ──────────────────────────────────────────────────
        cust_btn = tk.Button(
            right, text="🛍   Customer Login",
            font=("Segoe UI", 12, "bold"),
            bg=COLORS["primary"], fg="white",
            activebackground=COLORS["primary_hover"], activeforeground="white",
            relief="flat", width=22, height=2, cursor="hand2",
            command=self._open_customer_login
        )
        cust_btn.pack(pady=(0, 4))
        tk.Label(right, text="Browse, shop & track your orders",
                 font=FONTS["small"], bg=COLORS["bg"],
                 fg=COLORS["subtext"]).pack()

        # Divider
        div = tk.Frame(right, bg=COLORS["border"], height=1, width=260)
        div.pack(pady=22)

        # ── Admin button ─────────────────────────────────────────────────────
        admin_btn = tk.Button(
            right, text="⚙   Admin Portal",
            font=("Segoe UI", 12, "bold"),
            bg=COLORS["admin_top"], fg="white",
            activebackground=COLORS["admin_hover"], activeforeground="white",
            relief="flat", width=22, height=2, cursor="hand2",
            command=self._open_admin_login
        )
        admin_btn.pack(pady=(0, 4))
        tk.Label(right, text="Manage products, orders & reports",
                 font=FONTS["small"], bg=COLORS["bg"],
                 fg=COLORS["subtext"]).pack()

        # Demo hint
        hint = ("Demo  ▸  Customer: arjun@email.com / pass123\n"
                "          Admin:    admin@store.com / admin123")
        #tk.Label(right, text=hint,
        #         font=("Consolas", 8), bg=COLORS["bg"],
        #         fg="#94A3B8", justify="center").pack(side="bottom", pady=18)

    # ── Open portals ─────────────────────────────────────────────────────────
    def _open_customer_login(self):
        from gui.login import CustomerLoginWindow
        CustomerLoginWindow(self.root)

    def _open_admin_login(self):
        from gui.login import AdminLoginWindow
        AdminLoginWindow(self.root)

    def run(self):
        self.root.mainloop()
