import uuid
from datetime import date


class OrderItem:
    def __init__(self, smartphone, quantity, price):
        self.order_item_id = str(uuid.uuid4())[:8]
        self.smartphone = smartphone
        self.quantity = quantity
        self.price = price
        self.subtotal = self.calculate_subtotal()

    def calculate_subtotal(self):
        self.subtotal = round(self.price * self.quantity, 2)
        return self.subtotal

    def get_item_details(self):
        return (f"{self.smartphone.brand} {self.smartphone.model} "
                f"x{self.quantity} @ ${self.price:.2f} = ${self.subtotal:.2f}")


class Order:
    STATUSES = ["Pending", "Processing", "Shipped", "Delivered", "Cancelled"]

    def __init__(self, customer, cart_items):
        self.order_id = str(uuid.uuid4())[:8].upper()
        self.customer = customer
        self.order_items = [
            OrderItem(ci.smartphone, ci.quantity, ci.price) for ci in cart_items
        ]
        self.order_date = date.today()
        self.order_status = "Pending"
        self.shipping_address = customer.shipping_address
        self.total_amount = self.calculate_order_total()
        # Reduce stock
        for ci in cart_items:
            ci.smartphone.stock_quantity = max(0, ci.smartphone.stock_quantity - ci.quantity)

    def calculate_order_total(self):
        self.total_amount = round(sum(i.calculate_subtotal() for i in self.order_items), 2)
        return self.total_amount

    def update_order_status(self, status):
        if status in self.STATUSES:
            self.order_status = status

    def cancel_order(self):
        if self.order_status not in ["Shipped", "Delivered"]:
            for item in self.order_items:
                item.smartphone.stock_quantity += item.quantity
            self.order_status = "Cancelled"
            return True
        return False

    def get_order_details(self):
        sep = "-" * 44
        lines = [
            f"Order ID   : #{self.order_id}",
            f"Date       : {self.order_date}",
            f"Status     : {self.order_status}",
            f"Customer   : {self.customer.name}",
            f"Address    : {self.shipping_address}",
            sep,
            "Items:",
        ]
        for item in self.order_items:
            lines.append(f"  • {item.get_item_details()}")
        lines += [sep, f"  TOTAL      : ${self.total_amount:.2f}"]
        return "\n".join(lines)
