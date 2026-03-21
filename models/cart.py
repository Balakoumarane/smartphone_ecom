import uuid
from datetime import date


class CartItem:
    def __init__(self, smartphone, quantity):
        self.cart_item_id = str(uuid.uuid4())[:8]
        self.smartphone = smartphone
        self.quantity = quantity
        self.price = smartphone.price
        self.subtotal = self.calculate_subtotal()

    def update_quantity(self, quantity):
        self.quantity = quantity
        self.subtotal = self.calculate_subtotal()

    def calculate_subtotal(self):
        self.subtotal = round(self.price * self.quantity, 2)
        return self.subtotal

    def get_item_details(self):
        return (f"{self.smartphone.brand} {self.smartphone.model} "
                f"x{self.quantity} @ ${self.price:.2f} = ${self.subtotal:.2f}")


class Cart:
    def __init__(self, customer):
        self.cart_id = str(uuid.uuid4())[:8]
        self.customer = customer
        self.items = []
        self.total_price = 0.0
        self.created_date = date.today()

    def add_item(self, phone, quantity):
        for item in self.items:
            if item.smartphone.phone_id == phone.phone_id:
                item.update_quantity(item.quantity + quantity)
                self.calculate_total()
                return
        self.items.append(CartItem(phone, quantity))
        self.calculate_total()

    def remove_item(self, phone_id):
        self.items = [i for i in self.items if i.smartphone.phone_id != phone_id]
        self.calculate_total()

    def update_item_quantity(self, phone_id, quantity):
        for item in self.items:
            if item.smartphone.phone_id == phone_id:
                if quantity <= 0:
                    self.remove_item(phone_id)
                else:
                    item.update_quantity(quantity)
                break
        self.calculate_total()

    def calculate_total(self):
        self.total_price = round(sum(i.calculate_subtotal() for i in self.items), 2)
        return self.total_price

    def clear_cart(self):
        self.items = []
        self.total_price = 0.0

    def get_cart_items(self):
        return self.items
