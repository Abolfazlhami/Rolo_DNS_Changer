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