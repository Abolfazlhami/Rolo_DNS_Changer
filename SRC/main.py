# -*- coding: utf-8 -*-
"""
================================================================================
 main.py
 نقطه شروع اجرای برنامه — همین فایل را اجرا کن (python main.py)
================================================================================
"""
from admin_utils import ensure_admin, hide_console
from app import WifiApp

if __name__ == "__main__":
    ensure_admin()  # اگر ادمین نیست، پرامپت UAC نشان می‌دهد و دوباره اجرا می‌کند
    hide_console()  # پنجره‌ی سیاه CMD پشت برنامه رو مخفی می‌کند
    app = WifiApp()
    app.mainloop()