import random
import tkinter as tk
from datetime import datetime, timedelta
from tkinter import ttk, messagebox

from gui.theme import COLORS, FONTS


def format_inr(amount):
    return f"Rs {amount:,.0f}"


class _BaseDialog:
    def __init__(self, parent, title, geometry):
        self.result = None
        self.win = tk.Toplevel(parent)
        self.win.title(title)
        self.win.geometry(geometry)
        self.win.configure(bg=COLORS["bg"])
        self.win.resizable(False, False)
        self.win.transient(parent)
        self.win.grab_set()
        self.win.protocol("WM_DELETE_WINDOW", self._cancel)

    def _cancel(self):
        self.result = None
        self.win.destroy()

    def show(self):
        self.win.wait_window()
        return self.result


class UPIPaymentDialog(_BaseDialog):
    def __init__(self, parent, amount):
        super().__init__(parent, "UPI QR Checkout", "430x610")
        self.amount = amount
        self._timer_job = None
        self._transaction_ref = tk.StringVar()
        self._timer_var = tk.StringVar()
        self._payload_var = tk.StringVar()
        self._build()
        self._regenerate_qr()

    def _build(self):
        hdr = tk.Frame(self.win, bg=COLORS["primary"], height=62)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(
            hdr,
            text="UPI QR Payment",
            font=FONTS["heading"],
            bg=COLORS["primary"],
            fg="white",
        ).pack(expand=True)

        tk.Label(
            self.win,
            text=f"Scan this time-sensitive QR and confirm the UPI ref for {format_inr(self.amount)}.",
            font=FONTS["body"],
            bg=COLORS["bg"],
            fg=COLORS["text"],
            wraplength=360,
            justify="left",
        ).pack(anchor="w", padx=22, pady=(18, 10))

        self._canvas = tk.Canvas(
            self.win,
            width=220,
            height=220,
            bg="white",
            highlightthickness=1,
            highlightbackground=COLORS["border"],
        )
        self._canvas.pack(pady=6)

        tk.Label(
            self.win,
            textvariable=self._timer_var,
            font=FONTS["subheading"],
            bg=COLORS["bg"],
            fg=COLORS["warning"],
        ).pack()

        tk.Label(
            self.win,
            textvariable=self._payload_var,
            font=FONTS["small"],
            bg=COLORS["bg"],
            fg=COLORS["subtext"],
            wraplength=360,
            justify="left",
        ).pack(anchor="w", padx=22, pady=(10, 4))

        form = tk.Frame(self.win, bg=COLORS["bg"])
        form.pack(fill="x", padx=22, pady=6)
        tk.Label(
            form,
            text="UPI Transaction Ref",
            font=FONTS["subheading"],
            bg=COLORS["bg"],
            fg=COLORS["text"],
        ).pack(anchor="w")
        tk.Entry(
            form,
            textvariable=self._transaction_ref,
            font=FONTS["body"],
            relief="solid",
            bd=1,
        ).pack(fill="x", ipady=5, pady=(4, 0))

        actions = tk.Frame(self.win, bg=COLORS["bg"])
        actions.pack(fill="x", padx=22, pady=18)
        self._confirm_btn = tk.Button(
            actions,
            text="Confirm UPI Payment",
            font=FONTS["button"],
            bg=COLORS["success"],
            fg="white",
            relief="flat",
            padx=12,
            pady=8,
            cursor="hand2",
            command=self._submit,
        )
        self._confirm_btn.pack(side="left")
        tk.Button(
            actions,
            text="Regenerate QR",
            font=FONTS["button"],
            bg=COLORS["warning"],
            fg="white",
            relief="flat",
            padx=12,
            pady=8,
            cursor="hand2",
            command=self._regenerate_qr,
        ).pack(side="left", padx=8)
        tk.Button(
            actions,
            text="Cancel",
            font=FONTS["button"],
            bg=COLORS["error"],
            fg="white",
            relief="flat",
            padx=12,
            pady=8,
            cursor="hand2",
            command=self._cancel,
        ).pack(side="right")

    def _draw_qr(self, payload):
        self._canvas.delete("all")
        grid = 25
        size = 8
        pad = 10
        seed = sum(ord(ch) for ch in payload)
        rng = random.Random(seed)

        def draw_finder(x0, y0):
            self._canvas.create_rectangle(x0, y0, x0 + 7 * size, y0 + 7 * size, fill="black")
            self._canvas.create_rectangle(
                x0 + size,
                y0 + size,
                x0 + 6 * size,
                y0 + 6 * size,
                fill="white",
                outline="white",
            )
            self._canvas.create_rectangle(
                x0 + 2 * size,
                y0 + 2 * size,
                x0 + 5 * size,
                y0 + 5 * size,
                fill="black",
                outline="black",
            )

        draw_finder(pad, pad)
        draw_finder(pad + 15 * size, pad)
        draw_finder(pad, pad + 15 * size)

        reserved = set()
        for base_x, base_y in [(0, 0), (15, 0), (0, 15)]:
            for x in range(base_x, base_x + 7):
                for y in range(base_y, base_y + 7):
                    reserved.add((x, y))

        for x in range(grid):
            for y in range(grid):
                if (x, y) in reserved:
                    continue
                if rng.random() > 0.52:
                    x1 = pad + x * size
                    y1 = pad + y * size
                    self._canvas.create_rectangle(
                        x1, y1, x1 + size, y1 + size, fill="black", outline="black"
                    )

    def _regenerate_qr(self):
        self._expires_at = datetime.now() + timedelta(seconds=90)
        token = f"SMRT{random.randint(100000, 999999)}"
        self._payload = f"upi://pay?pn=SmartShop&am={int(self.amount)}&tr={token}"
        self._payload_var.set(
            "Virtual QR Payload:\n"
            f"{self._payload}\n"
            "Use any UPI app, then enter the generated reference below."
        )
        self._draw_qr(self._payload)
        self._confirm_btn.config(state="normal")
        self._tick()

    def _tick(self):
        if self._timer_job:
            self.win.after_cancel(self._timer_job)
        remaining = int((self._expires_at - datetime.now()).total_seconds())
        if remaining <= 0:
            self._timer_var.set("QR expired. Regenerate to continue.")
            self._confirm_btn.config(state="disabled")
            self._timer_job = None
            return
        self._timer_var.set(f"QR valid for {remaining} seconds")
        self._timer_job = self.win.after(500, self._tick)

    def _submit(self):
        if datetime.now() >= self._expires_at:
            messagebox.showerror("QR Expired", "Regenerate the QR and try again.", parent=self.win)
            return
        ref = self._transaction_ref.get().strip().upper()
        if len(ref) < 6:
            messagebox.showerror(
                "Invalid Reference",
                "Enter the UPI transaction reference shown in the payment app.",
                parent=self.win,
            )
            return
        self.result = {
            "gateway_name": "SmartShop UPI QR",
            "payment_details": (
                f"UPI ref {ref} captured from time-sensitive QR checkout. "
                f"Payload token expires at {self._expires_at.strftime('%H:%M:%S')}."
            ),
            "transaction_reference": ref,
            "note": "UPI payment confirmed by customer from the QR flow.",
        }
        self._cancel_timer()
        self.win.destroy()

    def _cancel_timer(self):
        if self._timer_job:
            self.win.after_cancel(self._timer_job)
            self._timer_job = None

    def _cancel(self):
        self._cancel_timer()
        super()._cancel()


class CardPaymentDialog(_BaseDialog):
    def __init__(self, parent, amount, method):
        super().__init__(parent, f"{method} Gateway", "430x520")
        self.amount = amount
        self.method = method
        self._vars = {key: tk.StringVar() for key in ["name", "card", "expiry", "cvv", "otp"]}
        self._build()

    def _build(self):
        gateway = "Razorpay Secure Gateway" if self.method == "Credit Card" else "BillDesk Card Gateway"
        hdr = tk.Frame(self.win, bg=COLORS["primary"], height=62)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text=gateway, font=FONTS["heading"], bg=COLORS["primary"], fg="white").pack(expand=True)

        body = tk.Frame(self.win, bg=COLORS["bg"], padx=24, pady=18)
        body.pack(fill="both", expand=True)
        tk.Label(
            body,
            text=f"Pay {format_inr(self.amount)} using your {self.method.lower()} details.",
            font=FONTS["body"],
            bg=COLORS["bg"],
            fg=COLORS["text"],
        ).pack(anchor="w", pady=(0, 12))

        fields = [
            ("Cardholder Name", "name", False),
            ("Card Number", "card", False),
            ("Expiry (MM/YY)", "expiry", False),
            ("CVV", "cvv", True),
            ("OTP", "otp", True),
        ]
        for label, key, masked in fields:
            tk.Label(body, text=label, font=FONTS["small"], bg=COLORS["bg"], fg=COLORS["text"]).pack(anchor="w", pady=(8, 2))
            tk.Entry(
                body,
                textvariable=self._vars[key],
                font=FONTS["body"],
                relief="solid",
                bd=1,
                show="*" if masked else "",
            ).pack(fill="x", ipady=5)

        actions = tk.Frame(body, bg=COLORS["bg"])
        actions.pack(fill="x", pady=18)
        tk.Button(
            actions,
            text="Pay Securely",
            font=FONTS["button"],
            bg=COLORS["success"],
            fg="white",
            relief="flat",
            padx=12,
            pady=8,
            cursor="hand2",
            command=self._submit,
        ).pack(side="left")
        tk.Button(
            actions,
            text="Cancel",
            font=FONTS["button"],
            bg=COLORS["error"],
            fg="white",
            relief="flat",
            padx=12,
            pady=8,
            cursor="hand2",
            command=self._cancel,
        ).pack(side="right")

    def _submit(self):
        name = self._vars["name"].get().strip()
        card = self._vars["card"].get().strip().replace(" ", "")
        expiry = self._vars["expiry"].get().strip()
        cvv = self._vars["cvv"].get().strip()
        otp = self._vars["otp"].get().strip()
        if not name or not card or not expiry or not cvv or not otp:
            messagebox.showerror("Missing Details", "Enter every card field to continue.", parent=self.win)
            return
        if not card.isdigit() or len(card) != 16:
            messagebox.showerror("Invalid Card", "Use a 16-digit card number.", parent=self.win)
            return
        if len(expiry) != 5 or expiry[2] != "/":
            messagebox.showerror("Invalid Expiry", "Use the MM/YY format.", parent=self.win)
            return
        if not cvv.isdigit() or len(cvv) != 3:
            messagebox.showerror("Invalid CVV", "Use a 3-digit CVV.", parent=self.win)
            return
        if not otp.isdigit() or len(otp) != 6:
            messagebox.showerror("Invalid OTP", "Use the 6-digit OTP.", parent=self.win)
            return
        gateway = "Razorpay Secure Gateway" if self.method == "Credit Card" else "BillDesk Card Gateway"
        masked = f"**** **** **** {card[-4:]}"
        self.result = {
            "gateway_name": gateway,
            "payment_details": f"{self.method} {masked} approved for {name}. OTP challenge passed.",
            "transaction_reference": f"CARD-{random.randint(100000, 999999)}",
            "note": f"{self.method} charge captured through the mock {gateway}.",
        }
        self.win.destroy()


class NetBankingDialog(_BaseDialog):
    def __init__(self, parent, amount):
        super().__init__(parent, "Net Banking Portal", "430x470")
        self.amount = amount
        self._bank = tk.StringVar(value="State Bank of India")
        self._user = tk.StringVar()
        self._password = tk.StringVar()
        self._pin = tk.StringVar()
        self._build()

    def _build(self):
        hdr = tk.Frame(self.win, bg=COLORS["admin_top"], height=62)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="Net Banking Gateway", font=FONTS["heading"], bg=COLORS["admin_top"], fg="white").pack(expand=True)

        body = tk.Frame(self.win, bg=COLORS["bg"], padx=24, pady=18)
        body.pack(fill="both", expand=True)
        tk.Label(
            body,
            text=f"Complete a mock bank transfer for {format_inr(self.amount)}.",
            font=FONTS["body"],
            bg=COLORS["bg"],
            fg=COLORS["text"],
        ).pack(anchor="w", pady=(0, 12))

        tk.Label(body, text="Bank", font=FONTS["small"], bg=COLORS["bg"], fg=COLORS["text"]).pack(anchor="w", pady=(8, 2))
        ttk.Combobox(
            body,
            textvariable=self._bank,
            values=["State Bank of India", "HDFC Bank", "ICICI Bank", "Axis Bank"],
            state="readonly",
        ).pack(fill="x", ipady=5)

        for label, var, secret in [
            ("Customer ID", self._user, False),
            ("Login Password", self._password, True),
            ("Transaction PIN", self._pin, True),
        ]:
            tk.Label(body, text=label, font=FONTS["small"], bg=COLORS["bg"], fg=COLORS["text"]).pack(anchor="w", pady=(8, 2))
            tk.Entry(body, textvariable=var, font=FONTS["body"], relief="solid", bd=1, show="*" if secret else "").pack(fill="x", ipady=5)

        actions = tk.Frame(body, bg=COLORS["bg"])
        actions.pack(fill="x", pady=18)
        tk.Button(
            actions,
            text="Authorize Transfer",
            font=FONTS["button"],
            bg=COLORS["success"],
            fg="white",
            relief="flat",
            padx=12,
            pady=8,
            cursor="hand2",
            command=self._submit,
        ).pack(side="left")
        tk.Button(
            actions,
            text="Cancel",
            font=FONTS["button"],
            bg=COLORS["error"],
            fg="white",
            relief="flat",
            padx=12,
            pady=8,
            cursor="hand2",
            command=self._cancel,
        ).pack(side="right")

    def _submit(self):
        user = self._user.get().strip()
        password = self._password.get().strip()
        pin = self._pin.get().strip()
        if not user or not password or not pin:
            messagebox.showerror("Missing Details", "Fill every banking field.", parent=self.win)
            return
        if not pin.isdigit() or len(pin) not in {4, 6}:
            messagebox.showerror("Invalid PIN", "Use a 4 or 6 digit transaction PIN.", parent=self.win)
            return
        bank = self._bank.get()
        self.result = {
            "gateway_name": "Net Banking Gateway",
            "payment_details": f"{bank} transfer authorized for customer id {user}.",
            "transaction_reference": f"NB-{random.randint(100000, 999999)}",
            "note": "Net banking transfer confirmed in the mock portal.",
        }
        self.win.destroy()


class RefundRequestDialog(_BaseDialog):
    def __init__(self, parent, payment):
        super().__init__(parent, "Refund Details", "430x420")
        self.payment = payment
        self._method = tk.StringVar()
        self._details = tk.StringVar()
        self._reason = tk.StringVar()
        self._build()

    def _build(self):
        hdr = tk.Frame(self.win, bg=COLORS["warning"], height=60)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="Refund Collection", font=FONTS["heading"], bg=COLORS["warning"], fg="white").pack(expand=True)

        paid = self.payment and self.payment.is_paid()
        methods = (
            ["Original Source", "UPI", "Bank Account", "Store Credit"]
            if paid else
            ["No Refund Needed", "UPI", "Bank Account"]
        )
        self._method.set(methods[0])

        body = tk.Frame(self.win, bg=COLORS["bg"], padx=24, pady=18)
        body.pack(fill="both", expand=True)
        tk.Label(
            body,
            text=(
                "Tell us how the refund should be routed."
                if paid else
                "This order was not fully paid yet. You can still record a refund preference."
            ),
            font=FONTS["body"],
            bg=COLORS["bg"],
            fg=COLORS["text"],
            wraplength=360,
            justify="left",
        ).pack(anchor="w", pady=(0, 12))

        tk.Label(body, text="Refund Method", font=FONTS["small"], bg=COLORS["bg"], fg=COLORS["text"]).pack(anchor="w", pady=(6, 2))
        ttk.Combobox(body, textvariable=self._method, values=methods, state="readonly").pack(fill="x", ipady=5)

        tk.Label(body, text="Refund Details", font=FONTS["small"], bg=COLORS["bg"], fg=COLORS["text"]).pack(anchor="w", pady=(8, 2))
        tk.Entry(body, textvariable=self._details, font=FONTS["body"], relief="solid", bd=1).pack(fill="x", ipady=5)

        tk.Label(body, text="Reason (optional)", font=FONTS["small"], bg=COLORS["bg"], fg=COLORS["text"]).pack(anchor="w", pady=(8, 2))
        tk.Entry(body, textvariable=self._reason, font=FONTS["body"], relief="solid", bd=1).pack(fill="x", ipady=5)

        actions = tk.Frame(body, bg=COLORS["bg"])
        actions.pack(fill="x", pady=18)
        tk.Button(
            actions,
            text="Submit",
            font=FONTS["button"],
            bg=COLORS["success"],
            fg="white",
            relief="flat",
            padx=12,
            pady=8,
            cursor="hand2",
            command=self._submit,
        ).pack(side="left")
        tk.Button(
            actions,
            text="Cancel",
            font=FONTS["button"],
            bg=COLORS["error"],
            fg="white",
            relief="flat",
            padx=12,
            pady=8,
            cursor="hand2",
            command=self._cancel,
        ).pack(side="right")

    def _submit(self):
        method = self._method.get().strip()
        details = self._details.get().strip()
        if method != "No Refund Needed" and not details:
            messagebox.showerror(
                "Missing Details",
                "Enter where the refund should be sent.",
                parent=self.win,
            )
            return
        note = self._reason.get().strip()
        self.result = {
            "method": method,
            "details": details or "No refund needed because payment was not captured.",
            "note": note,
        }
        self.win.destroy()


class PaymentVerificationDialog(_BaseDialog):
    def __init__(self, parent, payment):
        super().__init__(parent, "Verify Payment", "600x500")
        self.payment = payment
        self._choice = tk.StringVar(value="paid")
        self._note = tk.StringVar(value=payment.payment_note)
        self._build()

    def _build(self):
        hdr = tk.Frame(self.win, bg=COLORS["admin_top"], height=60)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="Admin Payment Verification", font=FONTS["heading"], bg=COLORS["admin_top"], fg="white").pack(expand=True)

        body = tk.Frame(self.win, bg=COLORS["bg"], padx=24, pady=18)
        body.pack(fill="both", expand=True)

        summary = [
            f"Method: {self.payment.payment_method}",
            f"Current Status: {self.payment.payment_status}",
            f"Customer Ref: {self.payment.transaction_reference}",
            f"Gateway: {self.payment.gateway_name or 'N/A'}",
            f"Details: {self.payment.payment_details or 'N/A'}",
        ]
        for line in summary:
            tk.Label(body, text=line, font=FONTS["body"], bg=COLORS["bg"], fg=COLORS["text"], wraplength=370, justify="left").pack(anchor="w", pady=2)

        tk.Label(body, text="Verification Result", font=FONTS["small"], bg=COLORS["bg"], fg=COLORS["text"]).pack(anchor="w", pady=(12, 4))
        for label, value in [
            ("Verified as paid", "paid"),
            ("Marked unpaid / failed", "unpaid"),
        ]:
            tk.Radiobutton(
                body,
                text=label,
                value=value,
                variable=self._choice,
                bg=COLORS["bg"],
                fg=COLORS["text"],
                selectcolor=COLORS["card"],
            ).pack(anchor="w")

        tk.Label(body, text="Admin Notes", font=FONTS["small"], bg=COLORS["bg"], fg=COLORS["text"]).pack(anchor="w", pady=(10, 2))
        tk.Entry(body, textvariable=self._note, font=FONTS["body"], relief="solid", bd=1).pack(fill="x", ipady=5)

        actions = tk.Frame(body, bg=COLORS["bg"])
        actions.pack(fill="x", pady=18)
        tk.Button(
            actions,
            text="Save Verification",
            font=FONTS["button"],
            bg=COLORS["success"],
            fg="white",
            relief="flat",
            padx=12,
            pady=8,
            cursor="hand2",
            command=self._submit,
        ).pack(side="left")
        tk.Button(
            actions,
            text="Cancel",
            font=FONTS["button"],
            bg=COLORS["error"],
            fg="white",
            relief="flat",
            padx=12,
            pady=8,
            cursor="hand2",
            command=self._cancel,
        ).pack(side="right")

    def _submit(self):
        self.result = {
            "is_paid": self._choice.get() == "paid",
            "note": self._note.get().strip(),
        }
        self.win.destroy()


class RefundProcessingDialog(_BaseDialog):
    def __init__(self, parent, payment):
        super().__init__(parent, "Process Refund", "620x460")
        self.payment = payment
        self._reference = tk.StringVar()
        self._note = tk.StringVar()
        self._build()

    def _build(self):
        hdr = tk.Frame(self.win, bg=COLORS["warning"], height=60)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(
            hdr,
            text="Admin Refund Processing",
            font=FONTS["heading"],
            bg=COLORS["warning"],
            fg="white",
        ).pack(expand=True)

        body = tk.Frame(self.win, bg=COLORS["bg"], padx=24, pady=18)
        body.pack(fill="both", expand=True)

        summary = [
            f"Payment Status: {self.payment.payment_status}",
            f"Refund Status: {self.payment.refund_status}",
            f"Requested Method: {self.payment.refund_method or 'N/A'}",
            f"Requested Details: {self.payment.refund_details or 'N/A'}",
            f"Requested On: {self.payment.refund_requested_at or 'N/A'}",
        ]
        for line in summary:
            tk.Label(
                body,
                text=line,
                font=FONTS["body"],
                bg=COLORS["bg"],
                fg=COLORS["text"],
                wraplength=520,
                justify="left",
            ).pack(anchor="w", pady=2)

        tk.Label(
            body,
            text="Refund Reference",
            font=FONTS["small"],
            bg=COLORS["bg"],
            fg=COLORS["text"],
        ).pack(anchor="w", pady=(14, 2))
        tk.Entry(
            body,
            textvariable=self._reference,
            font=FONTS["body"],
            relief="solid",
            bd=1,
        ).pack(fill="x", ipady=5)

        tk.Label(
            body,
            text="Admin Note",
            font=FONTS["small"],
            bg=COLORS["bg"],
            fg=COLORS["text"],
        ).pack(anchor="w", pady=(10, 2))
        tk.Entry(
            body,
            textvariable=self._note,
            font=FONTS["body"],
            relief="solid",
            bd=1,
        ).pack(fill="x", ipady=5)

        actions = tk.Frame(body, bg=COLORS["bg"])
        actions.pack(fill="x", pady=18)
        tk.Button(
            actions,
            text="Complete Refund",
            font=FONTS["button"],
            bg=COLORS["success"],
            fg="white",
            relief="flat",
            padx=12,
            pady=8,
            cursor="hand2",
            command=self._submit,
        ).pack(side="left")
        tk.Button(
            actions,
            text="Cancel",
            font=FONTS["button"],
            bg=COLORS["error"],
            fg="white",
            relief="flat",
            padx=12,
            pady=8,
            cursor="hand2",
            command=self._cancel,
        ).pack(side="right")

    def _submit(self):
        reference = self._reference.get().strip().upper()
        if not reference:
            messagebox.showerror(
                "Missing Reference",
                "Enter the refund reference before completing the refund.",
                parent=self.win,
            )
            return
        self.result = {
            "reference": reference,
            "note": self._note.get().strip(),
        }
        self.win.destroy()
