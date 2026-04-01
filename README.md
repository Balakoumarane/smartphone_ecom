# 📱 SmartShop — Smartphone E-Commerce & Billing System

A fully functional desktop e-commerce application built with **Python**, **Tkinter**, and **SQLite3**, simulating an online smartphone store with a complete customer shopping experience and admin management dashboard.

---

## 🚀 Features

### Customer Portal
- Register & login with secure authentication
- Browse 39 real smartphones with INR pricing
- Search by name / filter by category
- View detailed phone specifications
- Add to cart, update quantities, remove items
- Checkout with realistic payment simulation
- UPI QR flow, card/net banking portal simulation, and COD pending collection
- Admin-managed coupon code support with active/inactive control
- Wishlist support for later purchases
- Auto-generated invoice with tax (8%) calculation and PDF / PNG export
- Shipment tracking with courier & tracking number
- Order history with cancel, refund request, and invoice viewing
- Loyalty points redemption by customer choice and award on delivery
- Profile management & password change

### Admin Portal
- Secure admin login (separate from customer)
- Product Management — Add, Edit, Delete smartphones
- Order workspace with sidebar subtabs for Manage Orders and View Orders
- Order Management — update status, verify payments, and process refunds
- Customer Management — View all customers, toggle account status
- Coupon Management — add, remove, and toggle coupons
- Sales Report — KPIs, order breakdown, top-selling products
- Export sales report as PDF / PNG

### Backend
- **SQLite3** database — all data persists across sessions
- Auto-seeds 39 real phones, 7 categories on first run
- Full relational schema — 12 tables with foreign keys
- No data loss on app restart

---

## 🛠️ Tech Stack

| Layer       | Technology                                         |
|-------------|----------------------------------------------------|
| Language    | Python 3.x                                         |
| GUI         | Tkinter (ttk)                                      |
| Database    | SQLite3 (built-in)                                 |
| Exporting   | Pillow (PDF / PNG document rendering)              |
| OOP Concepts| Inheritance, Composition, Aggregation, Association |
| Architecture| MVC-style separation                               |

---

## 📁 Project Structure

```
smartshop_db/
├── main.py                  # Entry point
├── data/
│   ├── database.py          # SQLite manager — all CRUD operations
│   ├── store.py             # DB-backed Store singleton
│   └── smartshop.db         # Auto-created SQLite database (first run)
├── models/
│   ├── user.py              # User, Customer, Admin
│   ├── smartphone.py        # Smartphone, Category
│   ├── cart.py              # Cart, CartItem
│   ├── order.py             # Order, OrderItem
│   ├── coupon.py            # Coupon model
│   ├── payment.py           # Payment
│   ├── invoice.py           # Invoice / Bill
│   ├── shipment.py          # Shipment
│   └── report.py            # Report
├── utils/
│   ├── security.py          # Password hashing / verification
│   └── document_export.py   # PDF / PNG export helpers
└── gui/
    ├── theme.py             # Colors & fonts
    ├── home.py              # Home screen
    ├── login.py             # Login & Register windows
    ├── payment_workflows.py # Payment, verification, refund dialogs
    ├── customer_portal.py   # Full customer UI
    └── admin_portal.py      # Full admin UI
```

---

## ⚙️ Installation & Setup

### Prerequisites
- Python 3.8 or higher
- Pillow library for PDF / PNG export

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/Balakoumarane/smartphone_ecom.git
cd smartphone_ecom

# 2. Install dependency
pip install Pillow

# 3. Run the application
python main.py
```

> The SQLite database (`smartshop.db`) is created automatically on first launch and seeded with 39 smartphones and default accounts.

---

## 🔑 Default Credentials

| Role     | Email               | Password  |
|----------|---------------------|-----------|
| Customer | arjun@email.com     | pass123   |
| Admin    | admin@store.com     | admin123  |

---

## 🗄️ Database Schema

| Table              | Description                          |
|--------------------|--------------------------------------|
| `users`            | All user accounts with role          |
| `customers`        | Extended customer info & loyalty pts |
| `smartphones`      | Product catalog                      |
| `categories`       | Phone categories                     |
| `category_phones`  | Category ↔ Phone mapping             |
| `carts`            | Active cart per customer             |
| `cart_items`       | Items in each cart                   |
| `orders`           | Order headers                        |
| `order_items`      | Line items per order                 |
| `payments`         | Payment records                      |
| `invoices`         | Invoice & tax records                |
| `shipments`        | Shipment & tracking info             |

---

## 📦 Seeded Product Categories

| Category        | Price Range         |
|-----------------|---------------------|
| Flagship        | Above ₹80,000       |
| Upper Mid-Range | ₹50,000 – ₹80,000   |
| Mid-Range       | ₹30,000 – ₹50,000   |
| Budget          | Under ₹30,000       |
| Apple iPhones   | All iPhones         |
| Samsung Galaxy  | All Samsung phones  |
| OnePlus         | All OnePlus phones  |

---

## 🎓 OOP Concepts Demonstrated

| Concept       | Where Used                                         |
|---------------|----------------------------------------------------|
| Inheritance   | `Customer` and `Admin` inherit from `User`         |
| Composition   | `Cart` owns `CartItem`; `Order` owns `OrderItem`   |
| Aggregation   | `Category` references `Smartphone` objects         |
| Association   | `Order` linked to `Payment`, `Shipment`, `Invoice` |
| Encapsulation | Private attributes & methods in all classes        |

---

## 📄 License

This project is built for academic purposes as part of a Python Lab assignment.

---

*Built with Python · Tkinter · SQLite3 · OOP*
