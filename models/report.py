import uuid
from collections import Counter
from datetime import date

import numpy as np
import pandas as pd


class Report:
    def __init__(self, orders):
        self.report_id = f"RPT-{str(uuid.uuid4())[:6].upper()}"
        self.report_type = "Sales Report"
        self.generated_date = date.today()
        self.orders = list(orders)
        self.total_sales = 0.0
        self.total_orders = 0
        self.average_order_value = 0.0
        self.median_order_value = 0.0
        self.highest_order_value = 0.0
        self.revenue_std_dev = 0.0
        self.report_note = ""
        self._status_breakdown = {}
        self._generate()

    def _build_order_frame(self):
        rows = []
        for order in self.orders:
            rows.append(
                {
                    "order_id": getattr(order, "order_id", ""),
                    "customer_name": getattr(getattr(order, "customer", None), "name", "Unknown"),
                    "status": getattr(order, "order_status", "Pending"),
                    "total_amount": float(getattr(order, "total_amount", 0.0) or 0.0),
                    "order_date": str(getattr(order, "order_date", "")),
                    "item_count": int(
                        sum(getattr(item, "quantity", 0) for item in getattr(order, "order_items", []))
                    ),
                }
            )
        return pd.DataFrame(
            rows,
            columns=["order_id", "customer_name", "status", "total_amount", "order_date", "item_count"],
        )

    def _apply_metrics(self, frame):
        self.total_orders = int(len(frame))
        if frame.empty:
            self.total_sales = 0.0
            self.average_order_value = 0.0
            self.median_order_value = 0.0
            self.highest_order_value = 0.0
            self.revenue_std_dev = 0.0
            self._status_breakdown = {}
            return

        counts = frame["status"].value_counts().sort_index()
        self._status_breakdown = {str(status): int(count) for status, count in counts.items()}

        active_frame = frame[frame["status"] != "Cancelled"]
        amounts = (
            active_frame["total_amount"].to_numpy(dtype=float)
            if not active_frame.empty
            else np.array([], dtype=float)
        )
        if amounts.size:
            self.total_sales = round(float(np.sum(amounts)), 2)
            self.average_order_value = round(float(np.mean(amounts)), 2)
            self.median_order_value = round(float(np.median(amounts)), 2)
            self.highest_order_value = round(float(np.max(amounts)), 2)
            self.revenue_std_dev = round(float(np.std(amounts)), 2)
        else:
            self.total_sales = 0.0
            self.average_order_value = 0.0
            self.median_order_value = 0.0
            self.highest_order_value = 0.0
            self.revenue_std_dev = 0.0

    def _generate_fallback(self):
        active = [order for order in self.orders if getattr(order, "order_status", "") != "Cancelled"]
        amounts = np.array(
            [float(getattr(order, "total_amount", 0.0) or 0.0) for order in active],
            dtype=float,
        )
        self.total_orders = len(self.orders)
        self.total_sales = round(float(np.sum(amounts)), 2) if amounts.size else 0.0
        self.average_order_value = round(float(np.mean(amounts)), 2) if amounts.size else 0.0
        self.median_order_value = round(float(np.median(amounts)), 2) if amounts.size else 0.0
        self.highest_order_value = round(float(np.max(amounts)), 2) if amounts.size else 0.0
        self.revenue_std_dev = round(float(np.std(amounts)), 2) if amounts.size else 0.0
        self._status_breakdown = dict(
            Counter(getattr(order, "order_status", "Pending") for order in self.orders)
        )

    def _generate(self):
        try:
            frame = self._build_order_frame()
            self._apply_metrics(frame)
            self.report_note = "Analytics summary generated using pandas and numpy."
        except (AttributeError, KeyError, TypeError, ValueError) as exc:
            self._generate_fallback()
            self.report_note = f"Fallback analytics used because of inconsistent data: {exc}"

    def generate_sales_report(self, start_date=None, end_date=None):
        self._generate()

    def generate_product_report(self):
        return self.get_best_selling()

    def get_best_selling(self):
        try:
            rows = []
            for order in self.orders:
                if getattr(order, "order_status", "") == "Cancelled":
                    continue
                for item in getattr(order, "order_items", []):
                    phone = getattr(item, "smartphone", None)
                    rows.append(
                        {
                            "product_name": (
                                f"{getattr(phone, 'brand', 'Unknown')} {getattr(phone, 'model', 'Product')}"
                            ).strip(),
                            "quantity": int(getattr(item, "quantity", 0) or 0),
                        }
                    )
            if not rows:
                return []

            frame = pd.DataFrame(rows, columns=["product_name", "quantity"])
            grouped = (
                frame.groupby("product_name", as_index=False)["quantity"]
                .sum()
                .sort_values(by=["quantity", "product_name"], ascending=[False, True])
                .head(5)
            )
            return [(str(row["product_name"]), int(row["quantity"])) for _, row in grouped.iterrows()]
        except (AttributeError, KeyError, TypeError, ValueError):
            counter = Counter()
            for order in self.orders:
                if getattr(order, "order_status", "") != "Cancelled":
                    for item in getattr(order, "order_items", []):
                        name = f"{item.smartphone.brand} {item.smartphone.model}"
                        counter[name] += item.quantity
            return counter.most_common(5)

    def get_status_breakdown(self):
        return dict(self._status_breakdown)

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

    def export_report(self, format="txt"):
        self._generate()
        width = 52
        lines = [
            "=" * width,
            "SMARTSHOP - SALES REPORT".center(width),
            f"  Generated       : {self.generated_date}",
            f"  Report ID       : {self.report_id}",
            "=" * width,
            f"  Total Orders    : {self.total_orders}",
            f"  Total Revenue   : Rs {self.total_sales:.2f}",
            f"  Average Order   : Rs {self.average_order_value:.2f}",
            f"  Median Order    : Rs {self.median_order_value:.2f}",
            f"  Highest Order   : Rs {self.highest_order_value:.2f}",
            f"  Revenue Std Dev : Rs {self.revenue_std_dev:.2f}",
            "",
            "  Order Status Breakdown:",
        ]
        for status, count in self.get_status_breakdown().items():
            lines.append(f"    {status:<20}: {count}")
        lines += ["", "  Top 5 Best-Selling Products:"]
        best = self.get_best_selling()
        if best:
            for index, (name, qty) in enumerate(best, 1):
                lines.append(f"    {index}. {name} - {qty} unit(s)")
        else:
            lines.append("    No sales data yet.")
        lines += ["", f"  Note: {self.report_note}", "=" * width]
        return "\n".join(lines)
