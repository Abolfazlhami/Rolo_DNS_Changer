# -*- coding: utf-8 -*-
"""
================================================================================
 config.py
 رنگ‌ها، فونت‌ها و ثابت‌های ظاهری/عمومی برنامه
================================================================================
"""
import platform

BG_COLOR = "#0b1f3a"        # رنگ پس زمینه سورمه‌ای
CARD_COLOR = "#122a4d"      # رنگ کارت‌ها/باکس‌های داخلی
NAVY_LIGHT = "#1e4a80"      # سورمه‌ای روشن (رنگ هاور دکمه اسکن)
GREEN = "#27ae60"           # رنگ سبز اصلی دکمه‌ها
GREEN_HOVER = "#2ecc71"     # رنگ سبز روشن‌تر هنگام هاور
TEXT_COLOR = "#e6ecf5"      # رنگ متن اصلی
MUTED_COLOR = "#8fa3c2"     # رنگ متن کم‌رنگ/توضیحات

FONT_MAIN = ("Segoe UI", 10)
FONT_BOLD = ("Segoe UI", 12, "bold")

APP_VERSION_TEXT = "Rolo_IP_Dns_CH V1.0.0"   # برچسب نسخه گوشه پایین صفحه

IS_WINDOWS = platform.system() == "Windows"

SCAN_STEPS = ["IP", "IPv4", "IPv6", "Ping", "DNS", "Mac"]