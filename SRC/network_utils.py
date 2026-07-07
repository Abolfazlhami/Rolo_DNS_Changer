# -*- coding: utf-8 -*-
"""
================================================================================
 network_utils.py
 توابع کمکی شبکه: اسکن آداپتورها، خواندن/تغییر DNS و IP
================================================================================
"""
import subprocess
import re

from config import IS_WINDOWS

try:
    import psutil
except ImportError:
    psutil = None


def list_adapters():
    """لیست آداپتورهای فعال (up) روی سیستم"""
    adapters = []
    if psutil is None:
        return adapters
    stats = psutil.net_if_stats()
    for name, st in stats.items():
        if st.isup and name.lower() != "lo":
            adapters.append(name)
    return adapters


def get_adapter_info(name):
    """جمع‌آوری IPv4، IPv6 و MAC برای یک آداپتور مشخص"""
    info = {"ipv4": "-", "ipv6": "-", "mac": "-"}
    if psutil is None:
        return info
    import socket
    addrs = psutil.net_if_addrs().get(name, [])
    for a in addrs:
        if a.family == socket.AF_INET:
            info["ipv4"] = a.address
        elif a.family == socket.AF_INET6:
            info["ipv6"] = a.address.split("%")[0]
        elif a.family.name in ("AF_LINK", "AF_PACKET"):
            info["mac"] = a.address
    return info


def get_adapter_dns(name):
    """
    خواندن DNS اصلی و ثانویه آداپتور از طریق ipconfig /all (فقط ویندوز)
    خروجی: تاپل (dns_primary, dns_secondary) - اگه پیدا نشه "-" برمی‌گرده
    """
    if not IS_WINDOWS:
        return "-", "-"

    # الگو: خط "DNS Servers . . . : IP" و هر خط بعدیِ فقط-IP (بدون لیبل جدید) که زیرش میاد
    pattern = r"DNS Servers[.\s]*:\s*([0-9.]+)((?:\r?\n[ \t]+[0-9.]+)*)"

    def extract(block):
        m = re.search(pattern, block)
        if not m:
            return None
        primary = m.group(1)
        rest = re.findall(r"[0-9.]+", m.group(2) or "")
        secondary = rest[0] if rest else "-"
        return primary, secondary

    try:
        out = subprocess.check_output("ipconfig /all", shell=True,
                                       stderr=subprocess.DEVNULL,
                                       encoding="cp437", errors="ignore")
        blocks = re.split(r"\r?\n\r?\n", out)
        for block in blocks:
            if name in block:
                result = extract(block)
                if result:
                    return result
        result = extract(out)
        if result:
            return result
    except Exception:
        pass
    return "-", "-"


def ping_host(host="8.8.8.8"):
    """پینگ گرفتن و برگرداندن میانگین زمان به میلی‌ثانیه"""
    try:
        cmd = ["ping", "-n", "2", host] if IS_WINDOWS else ["ping", "-c", "2", host]
        out = subprocess.check_output(cmd, stderr=subprocess.DEVNULL,
                                       encoding="utf-8", errors="ignore", timeout=5)
        m = re.search(r"Average = (\d+)ms", out)
        if m:
            return m.group(1) + " ms"
        m = re.findall(r"time[=<]([\d.]+)", out)
        if m:
            avg = sum(float(x) for x in m) / len(m)
            return f"{avg:.0f} ms"
    except Exception:
        pass
    return "timeout"


def set_dns(adapter, dns_value, dns2_value=None):
    """
    اعمال DNS جدید روی آداپتور (نیازمند ادمین، فقط ویندوز)
    dns_value: DNS اصلی (الزامی)
    dns2_value: DNS ثانویه (اختیاری - اگه خالی/None باشه فقط DNS اصلی ست می‌شه)
    """
    if not IS_WINDOWS:
        return False, "این عملیات فقط روی ویندوز پشتیبانی می‌شود"
    try:
        # ست کردن DNS اصلی (static primary باعث می‌شه اگه DNS دومی از قبل بوده پاک بشه)
        cmd_primary = f'netsh interface ip set dns name="{adapter}" static {dns_value} primary'
        res = subprocess.run(cmd_primary, shell=True, capture_output=True, text=True)
        if res.returncode != 0:
            return False, res.stderr.strip() or "خطا در اعمال DNS اصلی (دسترسی ادمین لازم است)"

        # اگه DNS ثانویه هم داده شده، به عنوان DNS دوم اضافه‌اش کن
        if dns2_value:
            cmd_secondary = f'netsh interface ip add dns name="{adapter}" {dns2_value} index=2'
            res2 = subprocess.run(cmd_secondary, shell=True, capture_output=True, text=True)
            if res2.returncode != 0:
                return False, ("DNS اصلی تنظیم شد، اما DNS ثانویه با خطا مواجه شد: "
                                + (res2.stderr.strip() or "دسترسی ادمین لازم است"))

        return True, "DNS با موفقیت تغییر کرد"
    except Exception as e:
        return False, str(e)


def set_ip(adapter, ip_value, mask="255.255.255.0", gateway=None):
    """اعمال IP جدید روی آداپتور (نیازمند ادمین، فقط ویندوز)"""
    if not IS_WINDOWS:
        return False, "این عملیات فقط روی ویندوز پشتیبانی می‌شود"
    try:
        if gateway:
            cmd = f'netsh interface ip set address name="{adapter}" static {ip_value} {mask} {gateway}'
        else:
            cmd = f'netsh interface ip set address name="{adapter}" static {ip_value} {mask}'
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if res.returncode == 0:
            return True, "IP با موفقیت تغییر کرد"
        return False, res.stderr.strip() or "خطا در اعمال IP (دسترسی ادمین لازم است)"
    except Exception as e:
        return False, str(e)