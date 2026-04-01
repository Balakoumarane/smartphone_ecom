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

    def create_shipment(self, order):
        self.shipment_status = "Processing"

    def update_shipment_status(self, status):
        if status in self.STATUSES:
            self.shipment_status = status

    def track_shipment(self, tracking_number=None):
        eta = self.estimated_delivery if self.shipment_status != "Cancelled" else "Cancelled"
        return (
            f"Tracking Number   : {self.tracking_number}\n"
            f"Courier           : {self.courier_name}\n"
            f"Current Status    : {self.shipment_status}\n"
            f"Estimated Delivery: {eta}"
        )
