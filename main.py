"""
Smartphone E-Commerce & Billing System
=======================================
Entry point — run this file to launch the application.

Default credentials
-------------------
Customer : arjun@email.com  /  pass123
Admin    : admin@store.com /  admin123
"""

from gui.home import HomeWindow


if __name__ == "__main__":
    app = HomeWindow()
    app.run()
