# -*- coding: utf-8 -*-
"""
================================================================================
 ui_widgets.py
 ویجت‌های سفارشی: دکمه گرد (RoundButton)، اسپینر (Spinner)، کمبوی گرد (RoundedCombo)
================================================================================
"""
import tkinter as tk
from tkinter import ttk

from config import BG_COLOR, CARD_COLOR, GREEN, TEXT_COLOR, FONT_BOLD


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