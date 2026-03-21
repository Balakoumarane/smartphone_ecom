import uuid
from datetime import date


class Payment:
    def __init__(self, order, payment_method):
        self.payment_id = str(uuid.uuid4())[:8].upper()
        self.order = order
        self.payment_method = payment_method
        self.payment_status = "Pending"
        self.transaction_date = date.today()
        self.transaction_reference = f"TXN-{str(uuid.uuid4())[:6].upper()}"

    def process_payment(self, amount):
        self.payment_status = "Completed"
        return True

    def verify_payment(self, transaction_reference):
        return self.transaction_reference == transaction_reference

    def refund_payment(self, payment_id):
        self.payment_status = "Refunded"

    def generate_receipt(self):
        return (
            f"===== PAYMENT RECEIPT =====\n"
            f"Payment ID  : {self.payment_id}\n"
            f"Txn Ref     : {self.transaction_reference}\n"
            f"Method      : {self.payment_method}\n"
            f"Status      : {self.payment_status}\n"
            f"Date        : {self.transaction_date}\n"
            f"Amount      : ${self.order.total_amount:.2f}\n"
            f"==========================="
        )
