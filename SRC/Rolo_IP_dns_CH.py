# -*- coding: utf-8 -*-
"""
================================================================================
 WiFi Manager  |  Rolo_IP_Dns_CH
 نرم افزار نمایش اطلاعات آداپتور شبکه و تغییر DNS / IP
 نیازمند اجرا با دسترسی Administrator روی ویندوز برای اعمال تغییرات
================================================================================

فهرست بخش‌های کد (برای پیدا کردن سریع، اسم هر بخش را در فایل جستجو/Ctrl+F کن):

    [1]  IMPORTS ..................... ایمپورت‌های پایتون
    [2]  ADMIN ELEVATION (UAC) ........ درخواست خودکار دسترسی ادمین
    [3]  THEME & CONSTANTS ............ رنگ‌ها، فونت‌ها، ثابت‌های ظاهری
    [4]  NETWORK HELPER FUNCTIONS ..... توابع کمکی شبکه (اسکن/تغییر DNS و IP)
    [5]  UI HELPER WIDGETS ............ ویجت‌های سفارشی (دکمه گرد، اسپینر، کمبوی گرد)
    [6]  MAIN APPLICATION CLASS ....... کلاس اصلی برنامه (WifiApp)
           [6.1] BUILD: SELECT SCREEN .... ساخت صفحه انتخاب + دکمه اسکن
           [6.2] BUILD: RESULT SCREEN .... ساخت صفحه نمایش نتایج
           [6.3] SCAN LOGIC .............. منطق اسکن و انیمیشن لودینگ
           [6.4] SAVE DNS / SAVE IP ...... منطق ذخیره DNS و IP
    [7]  ENTRY POINT .................. نقطه شروع اجرای برنامه
================================================================================
"""

# ==============================================================================
# [1] IMPORTS
# ==============================================================================
import tkinter as tk
from tkinter import ttk
import threading
import subprocess
import platform
import re
import time
import os
import sys
import ctypes

try:
    import psutil
except ImportError:
    psutil = None


# ==============================================================================
# [2] ADMIN ELEVATION (UAC)
# ==============================================================================
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


# ==============================================================================
# [3] THEME & CONSTANTS
# ==============================================================================
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

SCAN_STEPS = ["IP", "IP4", "IP6", "Ping", "DNS", "Mac"]


# ==============================================================================
# [4] NETWORK HELPER FUNCTIONS
# ==============================================================================
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


# ==============================================================================
# [5] UI HELPER WIDGETS  (RoundButton, Spinner, RoundedCombo)
# ==============================================================================
def draw_round_rect(canvas, x1, y1, x2, y2, r, **kw):
    """رسم یک مستطیل با گوشه‌های گرد روی یک Canvas؛ توسط چند ویجت زیر استفاده می‌شود"""
    points = [x1+r, y1, x2-r, y1, x2, y1, x2, y1+r, x2, y2-r, x2, y2,
              x2-r, y2, x1+r, y2, x1, y2, x1, y2-r, x1, y1+r, x1, y1]
    return canvas.create_polygon(points, smooth=True, **kw)


def blend_colors(c1, c2, t):
    """ترکیب خطی دو رنگ هگز برای انیمیشن‌های fade و افکت نئون/گلو"""
    c1 = c1.lstrip("#")
    c2 = c2.lstrip("#")
    r1, g1, b1 = int(c1[0:2], 16), int(c1[2:4], 16), int(c1[4:6], 16)
    r2, g2, b2 = int(c2[0:2], 16), int(c2[2:4], 16), int(c2[4:6], 16)
    r = int(r1 + (r2 - r1) * t)
    g = int(g1 + (g2 - g1) * t)
    b = int(b1 + (b2 - b1) * t)
    return f"#{r:02x}{g:02x}{b:02x}"


class RoundButton(tk.Canvas):
    """
    دکمه گرد با ترانزیشن رنگی نرم در هاور (بدون بزرگ‌شدن، بدون نئون گرادیانی).
    رنگ پر/خط دور/متن به‌جای پرش ناگهانی، با یک انیمیشن کراس‌فید کوتاه بین
    حالت عادی و هاور تغییر می‌کنند. یک لایه بیرونی (رینگ) تکی هم می‌تواند
    فقط هنگام هاور نمایش داده شود (مثل دکمه REFRESH).
    """
    PAD = 14              # حاشیه اضافه؛ فقط برای جا شدن لایه بیرونی هاور کافیست
    ANIM_STEPS = 10        # تعداد فریم‌های انیمیشن کراس‌فید رنگ
    ANIM_INTERVAL_MS = 16  # فاصله هر فریم (~60 فریم بر ثانیه) => جمعاً ~160ms

    def __init__(self, parent, text, command, width=150, height=46, radius=23,
                 fill_normal=GREEN, fill_hover=GREEN,
                 border_normal=None, border_normal_width=0,
                 border_hover=None, border_hover_width=0,
                 text_color_normal="#ffffff", text_color_hover="#ffffff",
                 outer_ring_hover=None, outer_ring_gap=6, outer_ring_width=2,
                 font=FONT_BOLD, **kwargs):
        canvas_w = width + self.PAD * 2
        canvas_h = height + self.PAD * 2
        super().__init__(parent, width=canvas_w, height=canvas_h,
                          bg=BG_COLOR, highlightthickness=0, **kwargs)
        self.command = command
        self.width = width
        self.height = height
        self.radius = radius
        self.text = text
        self.font = font

        self.fill_normal = fill_normal
        self.fill_hover = fill_hover
        self.border_normal = border_normal or fill_normal
        self.border_normal_width = border_normal_width
        self.border_hover = border_hover or fill_hover
        self.border_hover_width = border_hover_width
        self.text_color_normal = text_color_normal
        self.text_color_hover = text_color_hover
        self.outer_ring_hover = outer_ring_hover
        self.outer_ring_gap = outer_ring_gap
        self.outer_ring_width = outer_ring_width

        self.hovered = False
        self.progress = 0.0        # 0 = عادی ، 1 = کاملاً هاور شده
        self._anim_after_id = None

        self._draw(0.0)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_click)

    def _draw(self, progress):
        self.delete("all")
        cx, cy = self.winfo_reqwidth() / 2, self.winfo_reqheight() / 2
        x1, y1 = cx - self.width / 2, cy - self.height / 2
        x2, y2 = cx + self.width / 2, cy + self.height / 2

        # لایه بیرونی سفید؛ با همان درصد پیشرفت به‌آرامی fade-in می‌شود
        if self.outer_ring_hover and progress > 0.01:
            gx1 = x1 - self.outer_ring_gap
            gy1 = y1 - self.outer_ring_gap
            gx2 = x2 + self.outer_ring_gap
            gy2 = y2 + self.outer_ring_gap
            ring_color = blend_colors(BG_COLOR, self.outer_ring_hover, progress)
            draw_round_rect(self, gx1, gy1, gx2, gy2, self.radius + self.outer_ring_gap,
                             fill="", outline=ring_color,
                             width=self.outer_ring_width)

        fill = blend_colors(self.fill_normal, self.fill_hover, progress)
        border_color = blend_colors(self.border_normal, self.border_hover, progress)
        border_width = self.border_normal_width + \
            (self.border_hover_width - self.border_normal_width) * progress
        text_color = blend_colors(self.text_color_normal, self.text_color_hover, progress)

        draw_round_rect(self, x1, y1, x2, y2, self.radius,
                         fill=fill, outline=border_color,
                         width=max(border_width, 0.1))
        self.create_text(cx, cy, text=self.text, fill=text_color, font=self.font)

    # -------- انیمیشن کراس‌فید نرم بین حالت عادی و هاور --------
    def _animate_to(self, target):
        if self._anim_after_id is not None:
            self.after_cancel(self._anim_after_id)
            self._anim_after_id = None
        self._step(target, self.progress, self.ANIM_STEPS)

    def _step(self, target, start, remaining):
        if remaining <= 0:
            self.progress = target
            self._draw(self.progress)
            self._anim_after_id = None
            return
        done = self.ANIM_STEPS - remaining + 1
        self.progress = start + (target - start) * (done / self.ANIM_STEPS)
        self._draw(self.progress)
        self._anim_after_id = self.after(
            self.ANIM_INTERVAL_MS, lambda: self._step(target, start, remaining - 1))

    def _on_enter(self, e):
        self.hovered = True
        self._animate_to(1.0)

    def _on_leave(self, e):
        self.hovered = False
        self._animate_to(0.0)

    def _on_click(self, e):
        if self.command:
            self.command()


class Spinner(tk.Canvas):
    """اسپینر دایره‌ای در حال چرخش برای صفحه لودینگ"""
    def __init__(self, parent, size=70, color=GREEN, **kwargs):
        super().__init__(parent, width=size, height=size,
                          bg=BG_COLOR, highlightthickness=0, **kwargs)
        self.size = size
        self.color = color
        self.angle = 0
        self.running = False

    def start(self):
        self.running = True
        self._animate()

    def stop(self):
        self.running = False
        self.delete("all")

    def _animate(self):
        if not self.running:
            return
        self.delete("all")
        pad = 6
        self.create_arc(pad, pad, self.size - pad, self.size - pad,
                         start=self.angle, extent=100,
                         style="arc", outline=self.color, width=5)
        self.angle = (self.angle + 12) % 360
        self.after(40, self._animate)


class RoundedCombo(tk.Frame):
    """
    باکس کشویی (Combobox) بزرگ‌تر با ظاهر گوشه‌گرد.
    ترفند: یک Canvas با مستطیل گوشه‌گرد به عنوان قاب پس‌زمینه رسم می‌شود و
    Combobox واقعی کمی کوچک‌تر و وسط آن قرار می‌گیرد؛ در نتیجه گوشه‌های
    گرد قاب از اطراف combobox بیرون می‌زنند و کل مجموعه گرد به نظر می‌رسد.
    """
    def __init__(self, parent, textvariable, width_px=300, height_px=48,
                 radius=18, font=("Segoe UI", 11)):
        super().__init__(parent, bg=BG_COLOR)
        self.canvas = tk.Canvas(self, width=width_px, height=height_px,
                                 bg=BG_COLOR, highlightthickness=0)
        self.canvas.pack()
        draw_round_rect(self.canvas, 1, 1, width_px - 1, height_px - 1,
                         radius, fill=CARD_COLOR, outline="")

        # استایل مخصوص combobox گرد (بدون حاشیه پیش‌فرض ویندوز)
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Rounded.TCombobox",
                        fieldbackground=CARD_COLOR,
                        background=CARD_COLOR,
                        foreground=TEXT_COLOR,
                        arrowcolor=TEXT_COLOR,
                        bordercolor=CARD_COLOR,
                        lightcolor=CARD_COLOR,
                        darkcolor=CARD_COLOR,
                        borderwidth=0,
                        relief="flat",
                        padding=6)
        style.map("Rounded.TCombobox",
                  fieldbackground=[("readonly", CARD_COLOR)],
                  background=[("readonly", CARD_COLOR)],
                  foreground=[("readonly", TEXT_COLOR)])

        # ظاهر لیست باز شونده (پاپ‌داون) نیز هم‌رنگ تم برنامه
        self.option_add("*TCombobox*Listbox.background", CARD_COLOR)
        self.option_add("*TCombobox*Listbox.foreground", TEXT_COLOR)
        self.option_add("*TCombobox*Listbox.selectBackground", GREEN)
        self.option_add("*TCombobox*Listbox.selectForeground", "white")
        self.option_add("*TCombobox*Listbox.font", font)

        self.combo = ttk.Combobox(self.canvas, textvariable=textvariable,
                                   state="readonly", font=font,
                                   style="Rounded.TCombobox", justify="center")
        inset_x, inset_y = 12, 8
        self.canvas.create_window(width_px / 2, height_px / 2, window=self.combo,
                                   width=width_px - inset_x * 2,
                                   height=height_px - inset_y * 2)

    def set_values(self, values):
        self.combo["values"] = values

    def set_current(self, index=0):
        if self.combo["values"]:
            self.combo.current(index)

    def get(self):
        return self.combo.get()


# ==============================================================================
# [6] MAIN APPLICATION CLASS (WifiApp)
# ==============================================================================
class WifiApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Rolo Scaner")
        self.geometry("500x500")
        self.resizable(False, False)
        self.configure(bg=BG_COLOR)

        self.current_adapter = None
        self.current_info = {}
        self.step_index = 0
        self.scanning = False

        self._build_main_screen()

    # --------------------------------------------------------------------
    # [6.1] BUILD: SELECT SCREEN  (انتخاب آداپتور + دکمه اسکن)
    # --------------------------------------------------------------------
    def _build_main_screen(self):
        # ظرف اصلی؛ همه صفحات (انتخاب/لودینگ/نتیجه) داخل این با place وسط‌چین می‌شوند
        self.container = tk.Frame(self, bg=BG_COLOR, width=500, height=500)
        self.container.pack(fill="both", expand=True)

        # ---- صفحه انتخاب + دکمه اسکن (وسط‌چین) ----
        self.select_frame = tk.Frame(self.container, bg=BG_COLOR)

        tk.Label(self.select_frame, text="Rolo Scaner", bg=BG_COLOR,
                 fg=TEXT_COLOR, font=("Segoe UI", 16, "bold")).pack(pady=(0, 25))

        tk.Label(self.select_frame, text="انتخاب اتصال", bg=BG_COLOR,
                 fg=MUTED_COLOR, font=FONT_MAIN).pack(pady=(0, 8))

        self.adapter_var = tk.StringVar()
        self.adapter_combo = RoundedCombo(self.select_frame, self.adapter_var,
                                           width_px=300, height_px=48, radius=18)
        self.adapter_combo.pack(pady=(0, 30))
        self._refresh_adapters()

        # ---- دکمه SCAN: سبز عادی -> سورمه‌ای روشن در هاور، با ترانزیشن نرم ----
        RoundButton(self.select_frame, "SCAN", self._start_scan,
                    width=150, height=46,
                    fill_normal=GREEN, fill_hover=NAVY_LIGHT,
                    border_normal="#ffffff", border_normal_width=2,
                    border_hover="#ffffff", border_hover_width=2,
                    text_color_normal="#ffffff", text_color_hover="#ffffff"
                    ).pack(pady=(0, 14))

        # ---- دکمه REFRESH: زرد -> قرمز در هاور، با لایه بیرونی سفید ----
        RoundButton(self.select_frame, "REFRESH", self._refresh_adapters,
                    width=130, height=38, radius=19,
                    fill_normal="#f1c40f", fill_hover="#e74c3c",
                    text_color_normal=BG_COLOR, text_color_hover="#ffffff",
                    outer_ring_hover="#ffffff", outer_ring_gap=6, outer_ring_width=2,
                    font=("Segoe UI", 10, "bold")
                    ).pack()

        self.select_frame.place(relx=0.5, rely=0.5, anchor="center")

        # ---- فریم لودینگ (وسط‌چین، مخفی) ----
        self.loading_frame = tk.Frame(self.container, bg=BG_COLOR)
        self.spinner = Spinner(self.loading_frame, size=70)
        self.spinner.pack(pady=(0, 18))
        self.loading_label = tk.Label(self.loading_frame, text="", bg=BG_COLOR,
                                       fg=TEXT_COLOR, font=("Segoe UI", 13, "bold"))
        self.loading_label.pack()

        # ---- فریم نتایج (وسط‌چین، مخفی) ----
        self.result_frame = tk.Frame(self.container, bg=BG_COLOR)
        self._build_result_widgets()

        # ---- برچسب نسخه؛ گوشه پایین سمت راست، همیشه روی صفحه باقی می‌ماند ----
        self.version_label = tk.Label(self.container, text=APP_VERSION_TEXT,
                                       bg=BG_COLOR, fg=MUTED_COLOR,
                                       font=("Segoe UI", 8))
        self.version_label.place(relx=1.0, rely=1.0, x=-10, y=-8, anchor="se")

    def _refresh_adapters(self):
        adapters = list_adapters()
        self.adapter_combo.set_values(adapters)
        if adapters:
            self.adapter_combo.set_current(0)

    # --------------------------------------------------------------------
    # [6.2] BUILD: RESULT SCREEN  (نمایش IP / IPv6 / MAC / Ping / DNS)
    # --------------------------------------------------------------------
    def _build_result_widgets(self):
        # کارت وسط‌چین با عرض ثابت که کل محتوای نتایج داخلش قرار می‌گیرد
        f = tk.Frame(self.result_frame, bg=BG_COLOR, width=380)

        def row(label_text):
            tk.Label(f, text=label_text, bg=BG_COLOR, fg=MUTED_COLOR,
                     font=("Segoe UI", 9)).pack(anchor="w", pady=(8, 2))

        row("IP")
        self.ip_entry = tk.Entry(f, font=FONT_MAIN, justify="center",
                                  state="readonly", readonlybackground=CARD_COLOR,
                                  fg=TEXT_COLOR, relief="flat")
        self.ip_entry.pack(fill="x", ipady=5)

        row("IPv6")
        self.ipv6_label = tk.Label(f, text="-", bg=CARD_COLOR, fg=TEXT_COLOR,
                                    font=FONT_MAIN, anchor="w")
        self.ipv6_label.pack(fill="x", ipady=5)

        row("MAC")
        self.mac_label = tk.Label(f, text="-", bg=CARD_COLOR, fg=TEXT_COLOR,
                                   font=FONT_MAIN, anchor="w")
        self.mac_label.pack(fill="x", ipady=5)

        row("Ping")
        self.ping_label = tk.Label(f, text="-", bg=CARD_COLOR, fg=TEXT_COLOR,
                                    font=FONT_MAIN, anchor="w")
        self.ping_label.pack(fill="x", ipady=5)

        row("DNS اصلی (قابل تغییر)")
        self.dns_entry = tk.Entry(f, font=FONT_MAIN, justify="center",
                                   bg=CARD_COLOR, fg=TEXT_COLOR,
                                   insertbackground=TEXT_COLOR, relief="flat")
        self.dns_entry.pack(fill="x", ipady=5)

        row("DNS ثانویه (اختیاری)")
        self.dns2_entry = tk.Entry(f, font=FONT_MAIN, justify="center",
                                    bg=CARD_COLOR, fg=TEXT_COLOR,
                                    insertbackground=TEXT_COLOR, relief="flat")
        self.dns2_entry.pack(fill="x", ipady=5)

        self.dns_msg = tk.Label(f, text="", bg=BG_COLOR, fg="#e74c3c",
                                 font=("Segoe UI", 8))
        self.dns_msg.pack(anchor="w")

        save_dns_btn = tk.Button(f, text="Save DNS", command=self._save_dns,
                                  bg=GREEN, fg="white", font=("Segoe UI", 8, "bold"),
                                  relief="flat", padx=8, pady=2, cursor="hand2")
        save_dns_btn.pack(anchor="e", pady=(2, 10))

        row("Change IP (دستی)")
        self.new_ip_entry = tk.Entry(f, font=FONT_MAIN, justify="center",
                                      bg=CARD_COLOR, fg=TEXT_COLOR,
                                      insertbackground=TEXT_COLOR, relief="flat")
        self.new_ip_entry.pack(fill="x", ipady=5)

        self.ip_msg = tk.Label(f, text="", bg=BG_COLOR, fg="#e74c3c",
                                font=("Segoe UI", 8))
        self.ip_msg.pack(anchor="w")

        save_ip_btn = tk.Button(f, text="Save IP", command=self._save_ip,
                                 bg=GREEN, fg="white", font=("Segoe UI", 8, "bold"),
                                 relief="flat", padx=8, pady=2, cursor="hand2")
        save_ip_btn.pack(anchor="e", pady=(2, 4))

        f.pack()

    # --------------------------------------------------------------------
    # [6.3] SCAN LOGIC  (اسکن، انیمیشن لودینگ، fade متن مراحل)
    # --------------------------------------------------------------------
    def _start_scan(self):
        adapter = self.adapter_var.get()
        if not adapter:
            return
        self.current_adapter = adapter

        self.select_frame.place_forget()
        self.result_frame.place_forget()
        self.loading_frame.place(relx=0.5, rely=0.5, anchor="center")
        self.spinner.start()
        self.scanning = True
        self.step_index = 0
        self._cycle_step_text()

        threading.Thread(target=self._do_scan, args=(adapter,), daemon=True).start()

    def _cycle_step_text(self):
        if not self.scanning:
            return
        text = SCAN_STEPS[self.step_index % len(SCAN_STEPS)]
        self._fade_text(text)
        self.step_index += 1
        self.after(650, self._cycle_step_text)

    def _fade_text(self, new_text):
        # انیمیشن ساده fade: محو شدن متن قبلی و پررنگ شدن متن بعدی
        steps = 8

        def fade_out(i=0):
            if i > steps:
                self.loading_label.config(text=new_text)
                fade_in()
                return
            gray = blend_colors(TEXT_COLOR, BG_COLOR, i / steps)
            self.loading_label.config(fg=gray)
            self.after(15, lambda: fade_out(i + 1))

        def fade_in(i=0):
            if i > steps:
                return
            gray = blend_colors(BG_COLOR, TEXT_COLOR, i / steps)
            self.loading_label.config(fg=gray)
            self.after(15, lambda: fade_in(i + 1))

        fade_out()

    def _do_scan(self, adapter):
        info = get_adapter_info(adapter)
        info["dns"], info["dns2"] = get_adapter_dns(adapter)
        info["ping"] = ping_host()
        time.sleep(3.2)  # اجازه بده انیمیشن مراحل کامل دیده شود
        self.after(0, lambda: self._show_results(info))

    def _show_results(self, info):
        self.scanning = False
        self.spinner.stop()
        self.loading_frame.place_forget()
        self.current_info = info

        self.ip_entry.config(state="normal")
        self.ip_entry.delete(0, "end")
        self.ip_entry.insert(0, info.get("ipv4", "-"))
        self.ip_entry.config(state="readonly")

        self.ipv6_label.config(text=info.get("ipv6", "-"))
        self.mac_label.config(text=info.get("mac", "-"))
        self.ping_label.config(text=info.get("ping", "-"))

        self.dns_entry.delete(0, "end")
        self.dns_entry.insert(0, info.get("dns", "-"))

        self.dns2_entry.delete(0, "end")
        dns2_val = info.get("dns2", "-")
        self.dns2_entry.insert(0, dns2_val if dns2_val != "-" else "")

        self.new_ip_entry.delete(0, "end")

        self.result_frame.place(relx=0.5, rely=0.5, anchor="center")

    # --------------------------------------------------------------------
    # [6.4] SAVE DNS / SAVE IP  (ذخیره تنظیمات روی آداپتور)
    # --------------------------------------------------------------------
    def _save_dns(self):
        new_dns = self.dns_entry.get().strip()
        new_dns2 = self.dns2_entry.get().strip()  # اختیاری - می‌تونه خالی باشه

        old_dns = self.current_info.get("dns", "-")
        old_dns2 = self.current_info.get("dns2", "-")
        old_dns2 = "" if old_dns2 == "-" else old_dns2

        if not new_dns:
            self.dns_msg.config(text="DNS اصلی نمی‌تواند خالی باشد", fg="#e74c3c")
            return
        if new_dns == old_dns and new_dns2 == old_dns2:
            self.dns_msg.config(text="DNS تغییری نکرده است", fg="#e74c3c")
            return

        ok, msg = set_dns(self.current_adapter, new_dns, new_dns2 or None)
        self.dns_msg.config(text=msg, fg="#2ecc71" if ok else "#e74c3c")
        if ok:
            self.current_info["dns"] = new_dns
            self.current_info["dns2"] = new_dns2 if new_dns2 else "-"

    def _save_ip(self):
        new_ip = self.new_ip_entry.get().strip()
        old_ip = self.current_info.get("ipv4", "-")
        if not new_ip or new_ip == old_ip:
            # طبق مشخصات: اگه همون قبلی بود هیچ کاری نکن (بدون ارور)
            return
        ok, msg = set_ip(self.current_adapter, new_ip)
        self.ip_msg.config(text=msg, fg="#2ecc71" if ok else "#e74c3c")
        if ok:
            self.current_info["ipv4"] = new_ip
            self.ip_entry.config(state="normal")
            self.ip_entry.delete(0, "end")
            self.ip_entry.insert(0, new_ip)
            self.ip_entry.config(state="readonly")


# ==============================================================================
# [7] ENTRY POINT
# ==============================================================================
if __name__ == "__main__":
    ensure_admin()  # اگر ادمین نیست، پرامپت UAC نشان می‌دهد و دوباره اجرا می‌کند
    app = WifiApp()
    app.mainloop()