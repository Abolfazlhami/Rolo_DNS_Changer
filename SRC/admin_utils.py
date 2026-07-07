# -*- coding: utf-8 -*-
"""
================================================================================
 admin_utils.py
 درخواست خودکار دسترسی ادمین (UAC) روی ویندوز
================================================================================
"""
import platform
import os
import sys
import ctypes


def is_admin():
    """بررسی می‌کند که آیا برنامه هم اکنون با دسترسی ادمین اجرا شده یا نه"""
    if platform.system() != "Windows":
        return True  # روی غیر ویندوز نیازی به این بررسی نیست
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def run_as_admin():
    """برنامه را با نمایش پرامپت UAC ویندوز و دسترسی ادمین دوباره اجرا می‌کند"""
    script = os.path.abspath(sys.argv[0])
    params = " ".join(f'"{a}"' for a in sys.argv[1:])
    try:
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, f'"{script}" {params}', None, 1
        )
    except Exception as e:
        print("خطا در اجرای با دسترسی ادمین:", e)
    sys.exit(0)


def ensure_admin():
    """اگر برنامه با دسترسی ادمین اجرا نشده باشد، پرامپت UAC را نشان می‌دهد"""
    if platform.system() == "Windows" and not is_admin():
        run_as_admin()