import uuid
import random
from datetime import date, timedelta


class Shipment:
    COURIERS = ["FedEx", "DHL", "UPS", "BlueDart", "Delhivery"]
    STATUSES = [
        "Order Placed", "Processing", "Dispatched",
        "In Transit", "Out for Delivery", "Delivered", "Cancelled"
    ]

    def __init__(self, order):
        self.shipment_id = f"SHP-{str(uuid.uuid4())[:6].upper()}"
        self.order = order
        self.courier_name = random.choice(self.COURIERS)
        prefix = self.courier_name[:3].upper()
        self.tracking_number = f"{prefix}-{str(uuid.uuid4())[:8].upper()}"
        self.shipment_status = "Order Placed"
        self.estimated_delivery = date.today() + timedelta(days=random.randint(3, 7))
        self.delivered_date = None

    def create_shipment(self, order):
        self.shipment_status = "Processing"

    def update_shipment_status(self, status):
        if status in self.STATUSES:
            self.shipment_status = status
            if status == "Delivered":
                self.delivered_date = date.today()
            elif status == "Cancelled":
                self.delivered_date = None

    def _display_status(self):
        if getattr(self.order, "order_status", "") == "Cancelled":
            return "Cancelled"
        if getattr(self.order, "order_status", "") == "Delivered":
            return "Delivered"
        return self.shipment_status

    def track_shipment(self, tracking_number=None):
        status = self._display_status()
        lines = [
            f"Tracking Number   : {self.tracking_number}\n"
            f"Courier           : {self.courier_name}\n"
            f"Current Status    : {status}"
        ]
        if status == "Delivered":
            delivered_on = self.delivered_date or self.estimated_delivery or date.today()
            lines.append(f"Delivered Date    : {delivered_on}")
        elif status != "Cancelled":
            lines.append(f"Estimated Delivery: {self.estimated_delivery}")
        return "\n".join(lines)
