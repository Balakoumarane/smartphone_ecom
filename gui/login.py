import tkinter as tk
from tkinter import ttk, messagebox
from gui.theme import COLORS, FONTS
from data.store import Store
from models.user import Customer
from models.cart import Cart


# ─────────────────────────────────────────────────────────────────────────────
class _BaseLogin:
    """Shared login form for Customer and Admin."""

    def __init__(self, parent, title, role, icon):
        self.store = Store()
        self.role  = role

        self.win = tk.Toplevel(parent)
        self.win.title(title)
        self.win.geometry("430x490")
        self.win.configure(bg=COLORS["bg"])
        self.win.resizable(False, False)
        self.win.grab_set()
        self._center(parent)
        self._build(title, icon)

    def _center(self, parent):
        self.win.update_idletasks()
        px = parent.winfo_x() + parent.winfo_width()  // 2
        py = parent.winfo_y() + parent.winfo_height() // 2
        w, h = 430, 490
        self.win.geometry(f"{w}x{h}+{px - w // 2}+{py - h // 2}")

    def _build(self, title, icon):
        # Header
        hdr_color = COLORS["primary"] if self.role == "customer" else COLORS["admin_top"]
        hdr = tk.Frame(self.win, bg=hdr_color, height=80)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text=f"{icon}  {title}",
                 font=FONTS["heading"], bg=hdr_color, fg="white").pack(expand=True)

        # Form
        frm = tk.Frame(self.win, bg=COLORS["bg"], padx=40)
        frm.pack(fill="both", expand=True, pady=10)

        tk.Label(frm, text="Email Address",
                 font=FONTS["subheading"], bg=COLORS["bg"],
                 fg=COLORS["text"]).pack(anchor="w", pady=(18, 3))
        self.email_var = tk.StringVar()
        tk.Entry(frm, textvariable=self.email_var, font=FONTS["body"],
                 bg=COLORS["entry_bg"], relief="solid", bd=1
                 ).pack(fill="x", ipady=7)

        tk.Label(frm, text="Password",
                 font=FONTS["subheading"], bg=COLORS["bg"],
                 fg=COLORS["text"]).pack(anchor="w", pady=(14, 3))
        self.pass_var = tk.StringVar()
        tk.Entry(frm, textvariable=self.pass_var, font=FONTS["body"],
                 bg=COLORS["entry_bg"], relief="solid", bd=1, show="●"
                 ).pack(fill="x", ipady=7)

        btn_color = COLORS["primary"] if self.role == "customer" else COLORS["admin_top"]
        tk.Button(frm, text="Login", font=FONTS["button"],
                  bg=btn_color, fg="white", relief="flat",
                  height=2, cursor="hand2",
                  command=self._login).pack(fill="x", pady=22)

        if self.role == "customer":
            row = tk.Frame(frm, bg=COLORS["bg"])
            row.pack()
            tk.Label(row, text="Don't have an account?",
                     font=FONTS["small"], bg=COLORS["bg"],
                     fg=COLORS["subtext"]).pack(side="left")
            tk.Button(row, text=" Register here", font=FONTS["small"],
                      bg=COLORS["bg"], fg=COLORS["primary"],
                      relief="flat", cursor="hand2",
                      command=self._open_register).pack(side="left")

    def _login(self):
        email    = self.email_var.get().strip()
        password = self.pass_var.get().strip()

        if not email or not password:
            messagebox.showerror("Error", "Please fill in all fields.",
                                 parent=self.win)
            return

        if self.role == "customer":
            user = self.store.get_customer_by_email(email)
        else:
            user = self.store.get_admin_by_email(email)

        if user and user.login(email, password):
            if user.account_status != "active":
                messagebox.showerror("Account Disabled",
                                     "Your account has been deactivated.",
                                     parent=self.win)
                return
            self.win.destroy()
            if self.role == "customer":
                from gui.customer_portal import CustomerPortal
                CustomerPortal(user, self.store)
            else:
                from gui.admin_portal import AdminPortal
                AdminPortal(user, self.store)
        else:
            messagebox.showerror("Login Failed",
                                 "Invalid email or password.",
                                 parent=self.win)

    def _open_register(self):
        RegisterWindow(self.win, self.store)


# ─────────────────────────────────────────────────────────────────────────────
class CustomerLoginWindow(_BaseLogin):
    def __init__(self, parent):
        super().__init__(parent, "Customer Login", "customer", "🛍")


class AdminLoginWindow(_BaseLogin):
    def __init__(self, parent):
        super().__init__(parent, "Admin Portal", "admin", "⚙")


# ─────────────────────────────────────────────────────────────────────────────
class RegisterWindow:
    def __init__(self, parent, store):
        self.store = store

        self.win = tk.Toplevel(parent)
        self.win.title("Create Account")
        self.win.geometry("450x530")
        self.win.configure(bg=COLORS["bg"])
        self.win.resizable(False, False)
        self.win.grab_set()
        self._build()

    def _build(self):
        hdr = tk.Frame(self.win, bg=COLORS["success"], height=70)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="✨  Create New Account",
                 font=FONTS["heading"], bg=COLORS["success"],
                 fg="white").pack(expand=True)

        frm = tk.Frame(self.win, bg=COLORS["bg"], padx=40)
        frm.pack(fill="both", expand=True, pady=10)

        labels  = ["Full Name", "Email Address", "Phone Number",
                   "Password", "Shipping Address"]
        secrets = [False, False, False, True, False]
        self._vars = []

        for lbl, secret in zip(labels, secrets):
            tk.Label(frm, text=lbl,
                     font=FONTS["subheading"], bg=COLORS["bg"],
                     fg=COLORS["text"]).pack(anchor="w", pady=(10, 2))
            var = tk.StringVar()
            tk.Entry(frm, textvariable=var, font=FONTS["body"],
                     bg=COLORS["entry_bg"], relief="solid", bd=1,
                     show="●" if secret else ""
                     ).pack(fill="x", ipady=5)
            self._vars.append(var)

        tk.Button(frm, text="Create Account",
                  font=FONTS["button"], bg=COLORS["success"], fg="white",
                  relief="flat", height=2, cursor="hand2",
                  command=self._register).pack(fill="x", pady=16)

    def _register(self):
        name, email, phone, password, address = [v.get().strip() for v in self._vars]

        if not all([name, email, phone, password]):
            messagebox.showerror("Error",
                                 "Name, email, phone and password are required.",
                                 parent=self.win)
            return
        if self.store.get_user_by_email(email):
            messagebox.showerror("Error",
                                 "An account with this email already exists.",
                                 parent=self.win)
            return

        customer = Customer(name, email, phone, password, address)
        customer.cart = Cart(customer)
        self.store.users.append(customer)

        messagebox.showinfo("Account Created!",
                            "Your account has been created.\nYou can now log in.",
                            parent=self.win)
        self.win.destroy()
