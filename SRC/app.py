# -*- coding: utf-8 -*-
"""
================================================================================
 app.py
 کلاس اصلی برنامه (WifiApp): صفحه ساده - انتخاب آداپتور، دو فیلد DNS،
 دکمه Set و دکمه Ping
================================================================================
"""
import tkinter as tk
import threading
import os

from config import (BG_COLOR, CARD_COLOR, NAVY_LIGHT, GREEN, TEXT_COLOR,
                     MUTED_COLOR, FONT_MAIN, APP_VERSION_TEXT)
from ui_widgets import RoundButton
from network_utils import list_adapters, get_adapter_dns, ping_host, set_dns


class WifiApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Rolo Scanner")
        self.geometry("400x340")
        self.resizable(False, False)
        self.configure(bg=BG_COLOR)
        self._set_window_icon()

        self.current_adapter = None

        self._build_main_screen()

    def _set_window_icon(self):
        try:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            candidate_paths = [
                os.path.join(base_dir, "rolo_icon.png"),
                os.path.join(base_dir, "assets", "rolo_icon.png"),
                os.path.join(base_dir, "assets", "icons", "rolo_icon.png"),
                os.path.join(base_dir, "..", "assets", "rolo_icon.png"),
                os.path.join(base_dir, "..", "assets", "icons", "rolo_icon.png"),
            ]
            icon_path = next((p for p in candidate_paths if os.path.exists(p)), None)
            if icon_path:
                self._icon_img = tk.PhotoImage(file=icon_path)
                self.iconphoto(True, self._icon_img)
            else:
                print("Warning: rolo_icon.png not found. Checked paths:")
                for p in candidate_paths:
                    print("  -", os.path.abspath(p))
        except Exception as e:
            print("Warning: Failed to set application icon:", e)

    def _build_main_screen(self):
        self.container = tk.Frame(self, bg=BG_COLOR, width=400, height=340)
        self.container.pack(fill="both", expand=True)

        main_frame = tk.Frame(self.container, bg=BG_COLOR)
        main_frame.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(main_frame, text="Rolo Scanner", bg=BG_COLOR,
                 fg=TEXT_COLOR, font=("Segoe UI", 16, "bold")).pack(pady=(0, 24))

        # آداپتور دیگه توی رابط کاربری انتخاب نمیشه؛ خودکار موقع Set پیدا میشه
        self._load_current_dns()

        # ---- DNS اول و دوم ----
        tk.Label(main_frame, text="Primary DNS", bg=BG_COLOR,
                 fg=MUTED_COLOR, font=FONT_MAIN).pack(anchor="w")
        self.dns_entry = tk.Entry(main_frame, font=FONT_MAIN, justify="center",
                                   bg=CARD_COLOR, fg=TEXT_COLOR, width=28,
                                   insertbackground=TEXT_COLOR, relief="flat")
        self.dns_entry.pack(ipady=6, pady=(2, 12))

        tk.Label(main_frame, text="Secondary DNS", bg=BG_COLOR,
                 fg=MUTED_COLOR, font=FONT_MAIN).pack(anchor="w")
        self.dns2_entry = tk.Entry(main_frame, font=FONT_MAIN, justify="center",
                                    bg=CARD_COLOR, fg=TEXT_COLOR, width=28,
                                    insertbackground=TEXT_COLOR, relief="flat")
        self.dns2_entry.pack(ipady=6, pady=(2, 16))

        # ---- دکمه‌ها: Set و Ping ----
        buttons_row = tk.Frame(main_frame, bg=BG_COLOR)
        buttons_row.pack(pady=(0, 12))

        RoundButton(buttons_row, "SET", self._save_dns,
                    width=110, height=42,
                    fill_normal=GREEN, fill_hover=NAVY_LIGHT,
                    text_color_normal="#ffffff", text_color_hover="#ffffff"
                    ).pack(side="left", padx=8)

        RoundButton(buttons_row, "PING", self._start_ping,
                    width=110, height=42,
                    fill_normal=NAVY_LIGHT, fill_hover=GREEN,
                    text_color_normal="#ffffff", text_color_hover="#ffffff"
                    ).pack(side="left", padx=8)

        # ---- پیام وضعیت ----
        self.status_label = tk.Label(main_frame, text="", bg=BG_COLOR,
                                      fg=TEXT_COLOR, font=("Segoe UI", 10, "bold"))
        self.status_label.pack(pady=(4, 0))

        self.version_label = tk.Label(self.container, text=APP_VERSION_TEXT,
                                       bg=BG_COLOR, fg=MUTED_COLOR,
                                       font=("Segoe UI", 8))
        self.version_label.place(relx=1.0, rely=1.0, x=-10, y=-8, anchor="se")

    def _get_active_adapter(self):
        """اولین آداپتور شبکه‌ی فعال رو خودکار پیدا می‌کنه (بدون نیاز به انتخاب دستی)"""
        adapters = list_adapters()
        return adapters[0] if adapters else None

    def _load_current_dns(self):
        adapter = self._get_active_adapter()
        if not adapter:
            return
        self.current_adapter = adapter
        dns, dns2 = get_adapter_dns(adapter)
        self.dns_entry.delete(0, "end")
        self.dns_entry.insert(0, dns if dns != "-" else "")
        self.dns2_entry.delete(0, "end")
        self.dns2_entry.insert(0, dns2 if dns2 != "-" else "")

    def _save_dns(self):
        adapter = self._get_active_adapter()
        if not adapter:
            self.status_label.config(text="No active adapter found", fg="#e74c3c")
            return

        new_dns = self.dns_entry.get().strip()
        new_dns2 = self.dns2_entry.get().strip()

        if not new_dns:
            self.status_label.config(text="Primary DNS cannot be empty", fg="#e74c3c")
            return

        self.current_adapter = adapter
        ok, msg = set_dns(adapter, new_dns, new_dns2 or None)
        self.status_label.config(text=msg, fg="#2ecc71" if ok else "#e74c3c")

    def _start_ping(self):
        self.status_label.config(text="Pinging...", fg=TEXT_COLOR)
        threading.Thread(target=self._do_ping, daemon=True).start()

    def _do_ping(self):
        result = ping_host()
        self.after(0, lambda: self.status_label.config(
            text=f"Ping: {result}", fg=TEXT_COLOR))