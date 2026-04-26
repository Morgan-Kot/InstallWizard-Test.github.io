# Calculator with button animations (bounce + darken) and numpy-generated beep sounds
# Dependencies: numpy, sounddevice (pip install numpy sounddevice)
# Animations use tkinter's .after() system - no extra libraries needed

import tkinter as tk
import numpy as np
import sounddevice as sd
import threading



LARGE_FONT_STYLE = ("Courier", 38, "bold")
SMALL_FONT_STYLE  = ("Courier", 14)
DIGITS_FONT_STYLE = ("Courier", 22, "bold")
DEFAULT_FONT_STYLE = ("Courier", 18)

BG_COLOR      = "#0D0D0D"
DISPLAY_BG    = "#141414"
DIGIT_BG      = "#1E1E1E"
DIGIT_HOVER   = "#2A2A2A"
OP_BG         = "#2A2A2A"
OP_HOVER      = "#3A3A3A"
EQUALS_BG     = "#00FF99"
EQUALS_HOVER  = "#00CC77"
TEXT_COLOR    = "#E8E8E8"
ACCENT_COLOR  = "#00FF99"
DIM_COLOR     = "#555555"


def play_beep(freq=440, duration=0.045, volume=0.18):
    def _play():
        sr = 44100
        t  = np.linspace(0, duration, int(sr * duration), False)
        wave = np.sin(2 * np.pi * freq * t)
        # Quick fade out so it doesn't click
        fade = np.linspace(1, 0, len(wave))
        wave = (wave * fade * volume).astype(np.float32)
        sd.play(wave, sr)
    threading.Thread(target=_play, daemon=True).start()


class AnimatedButton(tk.Button):
    def __init__(self, master, normal_bg, hover_bg, beep_freq=440, **kwargs):
        super().__init__(master, bg=normal_bg, activebackground=hover_bg,
                         relief="flat", borderwidth=0, cursor="hand2", **kwargs)
        self.normal_bg  = normal_bg
        self.hover_bg   = hover_bg
        self.beep_freq  = beep_freq
        self._orig_pady = kwargs.get("pady", 0)
        self.bind("<ButtonPress-1>",   self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<Enter>",           self._on_enter)
        self.bind("<Leave>",           self._on_leave)

    def _on_enter(self, _):
        self.config(bg=self.hover_bg)

    def _on_leave(self, _):
        self.config(bg=self.normal_bg)

    def _on_press(self, _):
        # Darken + shrink (bounce down)
        self.config(bg=self._darken(self.normal_bg, 0.55))
        self._bounce(shrink=True)
        play_beep(freq=self.beep_freq)

    def _on_release(self, _):
        self.config(bg=self.hover_bg)
        self._bounce(shrink=False)

    def _bounce(self, shrink):
        pad = 6 if shrink else 0
        self.config(padx=pad, pady=pad)
        self.after(120, lambda: self.config(padx=0, pady=0))

    @staticmethod
    def _darken(hex_color, factor):
        hex_color = hex_color.lstrip("#")
        r, g, b = (int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        r, g, b = (int(c * factor) for c in (r, g, b))
        return f"#{r:02x}{g:02x}{b:02x}"


class Calculator:
    def __init__(self):
        self.window = tk.Tk()
        self.window.geometry("500x660")
        #self.window.resizable(0, 0)
        self.window.title("Calculator")
        self.window.configure(bg=BG_COLOR)

        self.total_expression   = ""
        self.current_expression = ""

        self.display_frame = self._create_display_frame()
        self.total_label, self.label = self._create_display_labels()

        self.digits = {
            7: (1, 1), 8: (1, 2), 9: (1, 3),
            4: (2, 1), 5: (2, 2), 6: (2, 3),
            1: (3, 1), 2: (3, 2), 3: (3, 3),
            0: (4, 2), ".": (4, 1),
        }
        self.operations = {"/": "\u00F7", "*": "\u00D7", "-": "-", "+": "+"}

        self.buttons_frame = self._create_buttons_frame()
        self.buttons_frame.rowconfigure(0, weight=1)
        for x in range(1, 5):
            self.buttons_frame.rowconfigure(x, weight=1)
            self.buttons_frame.columnconfigure(x, weight=1)

        self._create_digit_buttons()
        self._create_operator_buttons()
        self._create_special_buttons()
        self._bind_keys()

    # ── Display ──────────────────────────────────────────────────────────────

    def _create_display_frame(self):
        frame = tk.Frame(self.window, height=180, bg=DISPLAY_BG,
                         highlightbackground=ACCENT_COLOR, highlightthickness=1)
        frame.pack(fill="x")
        return frame

    def _create_display_labels(self):
        total_label = tk.Label(
            self.display_frame, text="", anchor=tk.E,
            bg=DISPLAY_BG, fg=DIM_COLOR, padx=20, font=SMALL_FONT_STYLE)
        total_label.pack(expand=True, fill="both")

        label = tk.Label(
            self.display_frame, text="0", anchor=tk.E,
            bg=DISPLAY_BG, fg=TEXT_COLOR, padx=20, font=LARGE_FONT_STYLE)
        label.pack(expand=True, fill="both")
        return total_label, label

    def _create_buttons_frame(self):
        frame = tk.Frame(self.window, bg=BG_COLOR)
        frame.pack(expand=True, fill="both", pady=4)
        return frame

    # ── Buttons ───────────────────────────────────────────────────────────────

    def _make_btn(self, text, row, col, bg, hover, command, freq=440,
                  rowspan=1, colspan=1, fg=TEXT_COLOR, font=None):
        btn = AnimatedButton(
            self.buttons_frame,
            normal_bg=bg, hover_bg=hover,
            beep_freq=freq,
            text=text, fg=fg,
            font=font or DEFAULT_FONT_STYLE,
            command=command,
        )
        btn.grid(row=row, column=col, rowspan=rowspan, columnspan=colspan,
                 sticky=tk.NSEW, padx=2, pady=2)
        return btn

    def _create_digit_buttons(self):
        for digit, (row, col) in self.digits.items():
            self._make_btn(
                str(digit), row, col,
                DIGIT_BG, DIGIT_HOVER,
                lambda x=digit: self._add_to_expression(x),
                freq=520, font=DIGITS_FONT_STYLE,
            )

    def _create_operator_buttons(self):
        freqs = [380, 400, 420, 440]
        for i, (op, sym) in enumerate(self.operations.items()):
            self._make_btn(
                sym, i, 4,
                OP_BG, OP_HOVER,
                lambda x=op: self._append_operator(x),
                freq=freqs[i],
            )

    def _create_special_buttons(self):
        self._make_btn("C",        0, 1, OP_BG, OP_HOVER, self._clear,  freq=300)
        self._make_btn("x²",       0, 2, OP_BG, OP_HOVER, self._square, freq=600)
        self._make_btn("\u221ax",   0, 3, OP_BG, OP_HOVER, self._sqrt,   freq=650)
        # Equals — green accent
        self._make_btn(
            "=", 4, 3,
            EQUALS_BG, EQUALS_HOVER,
            self._evaluate,
            freq=700, colspan=2,
            fg="#0D0D0D", font=("Courier", 20, "bold"),
        )

    # ── Logic ─────────────────────────────────────────────────────────────────

    def _bind_keys(self):
        self.window.bind("<Return>", lambda _: self._evaluate())
        self.window.bind("<BackSpace>", lambda _: self._backspace())
        for key in self.digits:
            self.window.bind(str(key), lambda e, d=key: self._add_to_expression(d))
        for key in self.operations:
            self.window.bind(key, lambda e, op=key: self._append_operator(op))

    def _add_to_expression(self, value):
        self.current_expression += str(value)
        self._update_label()

    def _append_operator(self, operator):
        self.current_expression += operator
        self.total_expression   += self.current_expression
        self.current_expression  = ""
        self._update_total_label()
        self._update_label()

    def _clear(self):
        self.current_expression = ""
        self.total_expression   = ""
        self._update_label()
        self._update_total_label()

    def _backspace(self):
        self.current_expression = self.current_expression[:-1]
        self._update_label()

    def _square(self):
        try:
            self.current_expression = str(eval(f"{self.current_expression}**2"))
        except Exception:
            self.current_expression = "Error"
        self._update_label()

    def _sqrt(self):
        try:
            self.current_expression = str(eval(f"{self.current_expression}**0.5"))
        except Exception:
            self.current_expression = "Error"
        self._update_label()

    def _evaluate(self):
        self.total_expression += self.current_expression
        self._update_total_label()
        try:
            self.current_expression = str(eval(self.total_expression))
            self.total_expression   = ""
            self._flash_display()
        except Exception:
            self.current_expression = "Error"
        finally:
            self._update_label()

    def _flash_display(self):
        self.display_frame.config(highlightbackground="#00FF99", highlightthickness=2)
        self.window.after(200, lambda: self.display_frame.config(
            highlightbackground=ACCENT_COLOR, highlightthickness=1))

    # ── Label updates ─────────────────────────────────────────────────────────

    def _update_total_label(self):
        expr = self.total_expression
        for op, sym in self.operations.items():
            expr = expr.replace(op, f" {sym} ")
        self.total_label.config(text=expr)

    def _update_label(self):
        text = self.current_expression[:14] if self.current_expression else "0"
        self.label.config(text=text)

    def run(self):
        self.window.mainloop()


if __name__ == "__main__":
    calc = Calculator()
    calc.run()