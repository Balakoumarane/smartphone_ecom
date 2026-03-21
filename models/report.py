import uuid
from datetime import date
from collections import Counter


class Report:
    def __init__(self, orders):
        self.report_id = f"RPT-{str(uuid.uuid4())[:6].upper()}"
        self.report_type = "Sales Report"
        self.generated_date = date.today()
        self.orders = list(orders)
        self.total_sales = 0.0
        self.total_orders = 0
        self._generate()

    def _generate(self):
        active = [o for o in self.orders if o.order_status != "Cancelled"]
        self.total_orders = len(self.orders)
        self.total_sales = round(sum(o.total_amount for o in active), 2)

    def generate_sales_report(self, start_date=None, end_date=None):
        self._generate()

    def generate_product_report(self):
        return self.get_best_selling()

    def get_best_selling(self):
        counter = Counter()
        for order in self.orders:
            if order.order_status != "Cancelled":
                for item in order.order_items:
                    name = f"{item.smartphone.brand} {item.smartphone.model}"
                    counter[name] += item.quantity
        return counter.most_common(5)

    def get_status_breakdown(self):
        return dict(Counter(o.order_status for o in self.orders))

    def export_report(self, format="txt"):
        W = 50
        lines = [
            "=" * W,
            "         SMARTSHOP — SALES REPORT".center(W),
            f"  Generated : {self.generated_date}",
            f"  Report ID : {self.report_id}",
            "=" * W,
            f"  Total Orders  : {self.total_orders}",
            f"  Total Revenue : ${self.total_sales:.2f}",
            f"  Avg Order Val : ${self.total_sales / max(self.total_orders, 1):.2f}",
            "",
            "  Order Status Breakdown:",
        ]
        for status, count in self.get_status_breakdown().items():
            lines.append(f"    {status:<20}: {count}")
        lines += ["", "  Top 5 Best-Selling Products:"]
        best = self.get_best_selling()
        if best:
            for i, (name, qty) in enumerate(best, 1):
                lines.append(f"    {i}. {name}  —  {qty} unit(s)")
        else:
            lines.append("    No sales data yet.")
        lines.append("=" * W)
        return "\n".join(lines)
