import uuid
from datetime import date


class Coupon:
    def __init__(self, code, discount_percent, is_active=True):
        self.coupon_id = str(uuid.uuid4())[:8].upper()
        self.code = code.strip().upper()
        self.discount_percent = round(float(discount_percent), 2)
        self.is_active = bool(is_active)
        self.created_date = date.today()

    def toggle_active(self):
        self.is_active = not self.is_active

    def calculate_discount(self, subtotal):
        if not self.is_active:
            return 0.0
        return round(float(subtotal) * (self.discount_percent / 100.0), 2)

    def status_label(self):
        return "Active" if self.is_active else "Inactive"
