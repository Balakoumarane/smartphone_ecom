import uuid
from datetime import date


class Invoice:
    TAX_RATE = 0.08  # 8%

    def __init__(self, order, discount=0.0):
        self.invoice_id = f"INV-{str(uuid.uuid4())[:6].upper()}"
        self.order = order
        self.billing_date = date.today()
        self.discount = round(float(discount), 2)
        self.tax_amount = self.calculate_tax(order.total_amount - self.discount)
        self.total_amount = round(order.total_amount - self.discount + self.tax_amount, 2)

    def calculate_tax(self, amount):
        self.tax_amount = round(max(amount, 0) * self.TAX_RATE, 2)
        return self.tax_amount

    def apply_discount(self, amount):
        self.discount = round(float(amount), 2)
        self.tax_amount = self.calculate_tax(self.order.total_amount - self.discount)
        self.total_amount = round(self.order.total_amount - self.discount + self.tax_amount, 2)
        return self.total_amount

    def generate_invoice(self, order):
        pass  # handled in generate_invoice_text

    def generate_invoice_text(self):
        W = 52
        sep  = "=" * W
        dash = "-" * W
        lines = [
            sep,
            "         📱  SMARTSHOP  📱".center(W),
            "             INVOICE".center(W),
            sep,
            f"  Invoice ID  : {self.invoice_id}",
            f"  Order ID    : #{self.order.order_id}",
            f"  Date        : {self.billing_date}",
            f"  Customer    : {self.order.customer.name}",
            f"  Address     : {self.order.shipping_address}",
            dash,
            f"  {'Item':<26} {'Qty':>3} {'Price (₹)':>10} {'Total (₹)':>11}",
            dash,
        ]
        for item in self.order.order_items:
            name = f"{item.smartphone.brand} {item.smartphone.model}"
            if len(name) > 25:
                name = name[:23] + ".."
            lines.append(
                f"  {name:<26} {item.quantity:>3} {int(item.price):>9,} {int(item.subtotal):>10,}"
            )
        lines += [
            dash,
            f"  {'Subtotal':<36} {int(self.order.total_amount):>10,}",
            f"  {'Discount':<36} -{int(self.discount):>9,}",
            f"  {'Tax (8%)':<36} {int(self.tax_amount):>10,}",
            sep,
            f"  {'TOTAL AMOUNT':<36} {int(self.total_amount):>10,}",
            sep,
            "   Thank you for shopping at SmartShop!".center(W),
            sep,
        ]
        return "\n".join(lines)

    def print_invoice(self):
        print(self.generate_invoice_text())
