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
    adapters = []
    if psutil is None:
        return adapters
    stats = psutil.net_if_stats()
    for name, st in stats.items():
        if st.isup and name.lower() != "lo":
            adapters.append(name)
    return adapters


def get_adapter_info(name):
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
    if not IS_WINDOWS:
        return "-", "-"

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
    if not IS_WINDOWS:
        return False, "This operation is only supported on Windows"
    try:
        cmd_primary = f'netsh interface ip set dns name="{adapter}" static {dns_value} primary'
        res = subprocess.run(cmd_primary, shell=True, capture_output=True, text=True)
        if res.returncode != 0:
            return False, res.stderr.strip() or "Error setting Primary DNS (Admin privileges required)"

        if dns2_value:
            cmd_secondary = f'netsh interface ip add dns name="{adapter}" {dns2_value} index=2'
            res2 = subprocess.run(cmd_secondary, shell=True, capture_output=True, text=True)
            if res2.returncode != 0:
                return False, ("Primary DNS set, but Secondary DNS failed: "
                                + (res2.stderr.strip() or "Admin privileges required"))

        return True, "DNS updated successfully"
    except Exception as e:
        return False, str(e)


def set_ip(adapter, ip_value, mask="255.255.255.0", gateway=None):
    if not IS_WINDOWS:
        return False, "This operation is only supported on Windows"
    try:
        if gateway:
            cmd = f'netsh interface ip set address name="{adapter}" static {ip_value} {mask} {gateway}'
        else:
            cmd = f'netsh interface ip set address name="{adapter}" static {ip_value} {mask}'
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if res.returncode == 0:
            return True, "IP updated successfully"
        return False, res.stderr.strip() or "Error setting IP (Admin privileges required)"
    except Exception as e:
        return False, str(e)