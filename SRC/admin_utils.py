# -*- coding: utf-8 -*-
"""
================================================================================
 admin_utils.py
 درخواست خودکار دسترسی ادمین (UAC) روی ویندوز + مخفی کردن پنجره‌ی CMD
================================================================================
"""
import platform
import os
import sys
import ctypes


def is_admin():
    if platform.system() != "Windows":
        return True
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def run_as_admin():
    script = os.path.abspath(sys.argv[0])
    params = " ".join(f'"{a}"' for a in sys.argv[1:])
    try:
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, f'"{script}" {params}', None, 1
        )
    except Exception as e:
        print("Error executing with admin privileges:", e)
    sys.exit(0)


def ensure_admin():
    if platform.system() == "Windows" and not is_admin():
        run_as_admin()


def hide_console():
    """
    پنجره‌ی سیاه CMD که پشت برنامه باز می‌مونه رو مخفی می‌کنه (فقط ویندوز).
    وقتی برنامه با python.exe اجرا میشه یه کنسول پشتش باز میشه؛ این تابع
    اون پنجره رو با GetConsoleWindow + ShowWindow(SW_HIDE) پنهان می‌کنه.
    اگه برنامه با pythonw.exe یا exe ساخته‌شده با --noconsole اجرا بشه،
    اصلاً کنسولی وجود نداره و این تابع کاری انجام نمی‌ده.
    """
    if platform.system() != "Windows":
        return
    try:
        console_window = ctypes.windll.kernel32.GetConsoleWindow()
        if console_window:
            SW_HIDE = 0
            ctypes.windll.user32.ShowWindow(console_window, SW_HIDE)
    except Exception as e:
        print("Warning: Failed to hide console window:", e)