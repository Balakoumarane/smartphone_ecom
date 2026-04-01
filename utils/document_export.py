from pathlib import Path
import os

from PIL import Image, ImageDraw, ImageFont


PAGE_WIDTH = 1240
PAGE_HEIGHT = 2200
MARGIN = 70

COLORS = {
    "page": "#F8FAFC",
    "card": "#FFFFFF",
    "header": "#0F172A",
    "primary": "#1D4ED8",
    "success": "#16A34A",
    "warning": "#D97706",
    "text": "#0F172A",
    "muted": "#64748B",
    "border": "#CBD5E1",
    "row_alt": "#F8FAFC",
}

_FONT_CACHE = {}


def _format_inr(amount):
    return f"Rs {amount:,.0f}"


def _load_font(size, bold=False):
    key = (size, bold)
    if key in _FONT_CACHE:
        return _FONT_CACHE[key]

    font_dir = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts"
    names = (
        ["segoeuib.ttf", "arialbd.ttf", "calibrib.ttf", "arial.ttf"]
        if bold
        else ["segoeui.ttf", "arial.ttf", "calibri.ttf", "tahoma.ttf"]
    )
    for name in names:
        try:
            font = ImageFont.truetype(str(font_dir / name), size)
            _FONT_CACHE[key] = font
            return font
        except OSError:
            continue

    font = ImageFont.load_default()
    _FONT_CACHE[key] = font
    return font


def _line_height(font, extra=6):
    box = font.getbbox("Ag")
    return (box[3] - box[1]) + extra


def _text_width(draw, text, font):
    box = draw.textbbox((0, 0), text, font=font)
    return box[2] - box[0]


def _fit_text(draw, text, font, max_width):
    if _text_width(draw, text, font) <= max_width:
        return text
    trimmed = text
    ellipsis = "..."
    while trimmed and _text_width(draw, trimmed + ellipsis, font) > max_width:
        trimmed = trimmed[:-1]
    return (trimmed.rstrip() + ellipsis) if trimmed else ellipsis


def _wrap_text(draw, text, font, max_width):
    words = str(text).split()
    if not words:
        return [""]

    lines = []
    current = words[0]
    for word in words[1:]:
        candidate = f"{current} {word}"
        if _text_width(draw, candidate, font) <= max_width:
            current = candidate
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def _draw_card(draw, x1, y1, x2, y2, fill=None):
    draw.rounded_rectangle(
        (x1, y1, x2, y2),
        radius=18,
        fill=fill or COLORS["card"],
        outline=COLORS["border"],
        width=2,
    )


def _save_document(image, output_path):
    path = Path(output_path)
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        image.save(path, "PDF", resolution=100.0)
    elif suffix == ".png":
        image.save(path, "PNG")
    else:
        raise ValueError("Please choose a .pdf or .png file.")


def export_invoice_document(invoice, output_path):
    image = Image.new("RGB", (PAGE_WIDTH, PAGE_HEIGHT), COLORS["page"])
    draw = ImageDraw.Draw(image)

    title_font = _load_font(38, bold=True)
    heading_font = _load_font(24, bold=True)
    body_font = _load_font(20)
    strong_font = _load_font(20, bold=True)
    small_font = _load_font(16)

    header_bottom = MARGIN + 190
    draw.rounded_rectangle((MARGIN, MARGIN, PAGE_WIDTH - MARGIN, header_bottom), radius=24, fill=COLORS["header"])
    draw.text((MARGIN + 30, MARGIN + 28), "SmartShop Invoice", font=title_font, fill="white")
    draw.text(
        (MARGIN + 30, MARGIN + 102),
        f"Invoice ID: {invoice.invoice_id}    Order ID: #{invoice.order.order_id}",
        font=body_font,
        fill="#F8FAFC",
    )
    draw.text(
        (MARGIN + 30, MARGIN + 138),
        f"Billing Date: {invoice.billing_date}",
        font=body_font,
        fill="#E2E8F0",
    )

    y = header_bottom + 40
    _draw_card(draw, MARGIN, y, PAGE_WIDTH - MARGIN, y + 190)
    draw.text((MARGIN + 24, y + 20), "Billing To", font=heading_font, fill=COLORS["text"])
    draw.text((MARGIN + 24, y + 62), invoice.order.customer.name, font=strong_font, fill=COLORS["text"])
    addr_lines = _wrap_text(draw, invoice.order.shipping_address, body_font, 520)
    for idx, line in enumerate(addr_lines[:3]):
        draw.text((MARGIN + 24, y + 98 + idx * 28), line, font=body_font, fill=COLORS["muted"])

    right_x = MARGIN + 650
    meta_lines = [
        ("Order Date", invoice.order.order_date),
        ("Order Status", invoice.order.order_status),
        ("Items", len(invoice.order.order_items)),
        ("Customer ID", invoice.order.customer.user_id),
    ]
    for idx, (label, value) in enumerate(meta_lines):
        row_y = y + 28 + idx * 36
        draw.text((right_x, row_y), label, font=small_font, fill=COLORS["muted"])
        draw.text((right_x + 170, row_y - 2), str(value), font=body_font, fill=COLORS["text"])

    y += 230
    table_x = MARGIN
    table_w = PAGE_WIDTH - (MARGIN * 2)
    row_h = 48
    draw.rounded_rectangle((table_x, y, table_x + table_w, y + row_h), radius=16, fill=COLORS["primary"])
    headers = [("Item", 24), ("Qty", 660), ("Price", 780), ("Total", 980)]
    for title, x in headers:
        draw.text((table_x + x, y + 12), title, font=strong_font, fill="white")

    y += row_h + 8
    for idx, item in enumerate(invoice.order.order_items):
        fill = COLORS["card"] if idx % 2 == 0 else COLORS["row_alt"]
        draw.rounded_rectangle((table_x, y, table_x + table_w, y + row_h), radius=12, fill=fill, outline=COLORS["border"])
        item_name = _fit_text(
            draw,
            f"{item.smartphone.brand} {item.smartphone.model}",
            body_font,
            600,
        )
        draw.text((table_x + 24, y + 12), item_name, font=body_font, fill=COLORS["text"])
        draw.text((table_x + 670, y + 12), str(item.quantity), font=body_font, fill=COLORS["text"])
        draw.text((table_x + 780, y + 12), _format_inr(item.price), font=body_font, fill=COLORS["text"])
        draw.text((table_x + 980, y + 12), _format_inr(item.subtotal), font=body_font, fill=COLORS["text"])
        y += row_h + 8

    summary_y = y + 10
    summary_x1 = PAGE_WIDTH - MARGIN - 380
    _draw_card(draw, summary_x1, summary_y, PAGE_WIDTH - MARGIN, summary_y + 210)
    draw.text((summary_x1 + 24, summary_y + 18), "Payment Summary", font=heading_font, fill=COLORS["text"])

    summary_lines = [
        ("Subtotal", _format_inr(invoice.order.total_amount)),
        ("Discount", f"- {_format_inr(invoice.discount)}"),
        ("Tax (8%)", _format_inr(invoice.tax_amount)),
        ("Total Amount", _format_inr(invoice.total_amount)),
    ]
    for idx, (label, value) in enumerate(summary_lines):
        row_y = summary_y + 66 + idx * 34
        font = strong_font if label == "Total Amount" else body_font
        color = COLORS["primary"] if label == "Total Amount" else COLORS["text"]
        draw.text((summary_x1 + 24, row_y), label, font=font, fill=color)
        draw.text((summary_x1 + 210, row_y), value, font=font, fill=color)

    footer_y = summary_y + 250
    draw.text((MARGIN, footer_y), "Thank you for shopping with SmartShop.", font=body_font, fill=COLORS["success"])
    draw.text((MARGIN, footer_y + 34), "This invoice was generated digitally and can be used for order reference.", font=small_font, fill=COLORS["muted"])

    final_height = min(max(footer_y + 110, 980), PAGE_HEIGHT)
    _save_document(image.crop((0, 0, PAGE_WIDTH, final_height)), output_path)


def export_sales_report_document(report, output_path):
    image = Image.new("RGB", (PAGE_WIDTH, PAGE_HEIGHT), COLORS["page"])
    draw = ImageDraw.Draw(image)

    title_font = _load_font(38, bold=True)
    heading_font = _load_font(24, bold=True)
    body_font = _load_font(20)
    strong_font = _load_font(20, bold=True)
    small_font = _load_font(16)

    header_bottom = MARGIN + 190
    draw.rounded_rectangle((MARGIN, MARGIN, PAGE_WIDTH - MARGIN, header_bottom), radius=24, fill=COLORS["header"])
    draw.text((MARGIN + 30, MARGIN + 28), "SmartShop Sales Report", font=title_font, fill="white")
    draw.text(
        (MARGIN + 30, MARGIN + 102),
        f"Report ID: {report.report_id}",
        font=body_font,
        fill="#F8FAFC",
    )
    draw.text(
        (MARGIN + 30, MARGIN + 138),
        f"Generated Date: {report.generated_date}",
        font=body_font,
        fill="#E2E8F0",
    )

    card_y = header_bottom + 40
    card_w = 250
    gap = 24
    stats = [
        ("Total Orders", str(report.total_orders), COLORS["primary"]),
        ("Active Revenue", _format_inr(report.total_sales), COLORS["success"]),
        ("Average Order", _format_inr(report.total_sales / max(report.total_orders, 1)), "#0EA5E9"),
        ("Cancelled Orders", str(report.get_status_breakdown().get("Cancelled", 0)), COLORS["warning"]),
    ]
    for idx, (label, value, color) in enumerate(stats):
        x1 = MARGIN + idx * (card_w + gap)
        x2 = x1 + card_w
        _draw_card(draw, x1, card_y, x2, card_y + 140)
        draw.text((x1 + 24, card_y + 24), label, font=small_font, fill=COLORS["muted"])
        draw.text((x1 + 24, card_y + 70), value, font=_load_font(28, bold=True), fill=color)

    left_x1 = MARGIN
    left_x2 = 610
    right_x1 = 640
    right_x2 = PAGE_WIDTH - MARGIN
    body_y = card_y + 180

    status_breakdown = report.get_status_breakdown()
    best_selling = report.get_best_selling()

    left_height = 150 + max(len(status_breakdown), 1) * 34
    right_height = 150 + max(len(best_selling), 1) * 34
    panel_height = max(left_height, right_height)

    _draw_card(draw, left_x1, body_y, left_x2, body_y + panel_height)
    _draw_card(draw, right_x1, body_y, right_x2, body_y + panel_height)

    draw.text((left_x1 + 24, body_y + 22), "Order Status Breakdown", font=heading_font, fill=COLORS["text"])
    line_y = body_y + 72
    if status_breakdown:
        for status, count in status_breakdown.items():
            draw.text((left_x1 + 24, line_y), status, font=body_font, fill=COLORS["text"])
            draw.text((left_x2 - 120, line_y), str(count), font=strong_font, fill=COLORS["primary"])
            line_y += 34
    else:
        draw.text((left_x1 + 24, line_y), "No order data available.", font=body_font, fill=COLORS["muted"])

    draw.text((right_x1 + 24, body_y + 22), "Top Selling Products", font=heading_font, fill=COLORS["text"])
    line_y = body_y + 72
    if best_selling:
        for idx, (name, qty) in enumerate(best_selling, 1):
            label = _fit_text(draw, f"{idx}. {name}", body_font, 360)
            draw.text((right_x1 + 24, line_y), label, font=body_font, fill=COLORS["text"])
            draw.text((right_x2 - 120, line_y), f"{qty} sold", font=strong_font, fill=COLORS["success"])
            line_y += 34
    else:
        draw.text((right_x1 + 24, line_y), "No sales data available.", font=body_font, fill=COLORS["muted"])

    y = body_y + panel_height + 30
    _draw_card(draw, MARGIN, y, PAGE_WIDTH - MARGIN, y + 150)
    draw.text((MARGIN + 24, y + 20), "Notes", font=heading_font, fill=COLORS["text"])
    notes = [
        "Cancelled orders are excluded from active revenue.",
        "Average order value is based on the total number of orders in the report.",
        "This report is generated from the current SmartShop database snapshot.",
    ]
    for idx, note in enumerate(notes):
        draw.text((MARGIN + 24, y + 62 + idx * 28), f"- {note}", font=body_font, fill=COLORS["muted"])

    final_height = min(max(y + 200, 980), PAGE_HEIGHT)
    _save_document(image.crop((0, 0, PAGE_WIDTH, final_height)), output_path)
