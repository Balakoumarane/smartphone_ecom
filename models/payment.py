import uuid
from datetime import date


class Payment:
    ONLINE_METHODS = {"Credit Card", "Debit Card", "UPI", "Net Banking"}

    def __init__(self, order, payment_method):
        self.payment_id = str(uuid.uuid4())[:8].upper()
        self.order = order
        self.payment_method = payment_method
        self.payment_status = "Pending"
        self.transaction_date = str(date.today())
        self.transaction_reference = f"TXN-{str(uuid.uuid4())[:6].upper()}"
        self.gateway_name = ""
        self.payment_details = ""
        self.payment_note = ""
        self.verification_status = "Pending"
        self.verified_by = ""
        self.verified_at = ""
        self.refund_status = "Not Requested"
        self.refund_method = ""
        self.refund_details = ""
        self.refund_requested_at = ""
        self.refund_reference = ""
        self.refund_processed_by = ""
        self.refund_processed_at = ""

    def process_payment(
        self,
        amount,
        *,
        gateway_name="",
        payment_details="",
        note="",
        transaction_reference=None,
    ):
        self.gateway_name = gateway_name
        self.payment_details = payment_details
        self.payment_note = note
        if transaction_reference:
            self.transaction_reference = transaction_reference

        if self.payment_method == "Cash on Delivery":
            self.payment_status = "Pending on Delivery"
            self.gateway_name = gateway_name or "Cash Collection"
            self.payment_details = payment_details or (
                f"Collect Rs {amount:,.2f} when the shipment reaches the customer."
            )
            self.payment_note = note or "Cash will be collected at delivery time."
            return True

        self.payment_status = "Completed"
        return True

    def verify_payment(self, admin_name, is_paid, note=""):
        self.verified_by = admin_name
        self.verified_at = str(date.today())
        self.payment_note = note or self.payment_note
        if is_paid:
            self.payment_status = "Completed"
            self.verification_status = "Verified"
        else:
            self.payment_status = "Failed"
            self.verification_status = "Rejected"

    def request_refund(self, method, details):
        self.refund_method = method
        self.refund_details = details
        self.refund_requested_at = str(date.today())
        if self.payment_status == "Completed":
            self.refund_status = "Pending"
            self.payment_status = "Refund Pending"
        else:
            self.refund_status = "Not Needed"
            self.payment_status = "Cancelled"

    def refund_payment(self, admin_name="", refund_reference="", note=""):
        self.payment_status = "Refunded"
        self.refund_status = "Completed"
        self.refund_reference = refund_reference
        self.refund_processed_by = admin_name
        self.refund_processed_at = str(date.today())
        if note:
            self.payment_note = note

    def is_paid(self):
        return self.payment_status in {"Completed", "Refund Pending", "Refunded"}

    def verification_label(self):
        return self.verification_status

    def refund_label(self):
        return self.refund_status

    def generate_receipt(self):
        return (
            f"===== PAYMENT RECEIPT =====\n"
            f"Payment ID    : {self.payment_id}\n"
            f"Txn Ref       : {self.transaction_reference}\n"
            f"Method        : {self.payment_method}\n"
            f"Gateway       : {self.gateway_name or 'N/A'}\n"
            f"Status        : {self.payment_status}\n"
            f"Verified      : {self.verification_status}\n"
            f"Date          : {self.transaction_date}\n"
            f"Amount        : Rs {self.order.total_amount:,.2f}\n"
            f"Details       : {self.payment_details or 'N/A'}\n"
            f"Refund Status : {self.refund_status}\n"
            f"Refund Method : {self.refund_method or 'N/A'}\n"
            f"Refund Ref    : {self.refund_reference or 'N/A'}\n"
            f"Refund By     : {self.refund_processed_by or 'N/A'}\n"
            f"==========================="
        )
