# -*- coding: utf-8 -*-
"""
================================================================================
 app.py
 کلاس اصلی برنامه (WifiApp): ساخت صفحات، منطق اسکن، ذخیره DNS/IP
================================================================================
"""
import tkinter as tk
import threading
import time

from config import (BG_COLOR, CARD_COLOR, NAVY_LIGHT, GREEN, TEXT_COLOR,
                     MUTED_COLOR, FONT_MAIN, APP_VERSION_TEXT, SCAN_STEPS)
from ui_widgets import RoundButton, Spinner, RoundedCombo, blend_colors
from network_utils import list_adapters, get_adapter_info, get_adapter_dns, ping_host, set_dns, set_ip


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

        tk.Label(self.select_frame, text="انتخاب کارت شبکه", bg=BG_COLOR,
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