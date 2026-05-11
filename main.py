import customtkinter as ctk
import secrets
import string
import re

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class PasswordGeneratorTab(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self._build_ui()

    def _build_ui(self):
        ctk.CTkLabel(self, text="Password Generator",
                     font=ctk.CTkFont(size=22, weight="bold")).pack(pady=(20, 4))
        ctk.CTkLabel(self, text="Customise and generate a secure password.",
                     text_color="gray").pack(pady=(0, 20))

        card = ctk.CTkFrame(self, corner_radius=12)
        card.pack(padx=40, pady=8, fill="x")

        length_row = ctk.CTkFrame(card, fg_color="transparent")
        length_row.pack(fill="x", padx=20, pady=(16, 4))
        ctk.CTkLabel(length_row, text="Length:", width=120, anchor="w").pack(side="left")
        self._length_var = ctk.IntVar(value=16)
        self._length_label = ctk.CTkLabel(length_row, text="16", width=30)
        self._length_label.pack(side="right")
        slider = ctk.CTkSlider(length_row, from_=8, to=64, number_of_steps=56,
                               variable=self._length_var,
                               command=self._on_length_change)
        slider.pack(side="left", fill="x", expand=True, padx=10)

        
        opts = ctk.CTkFrame(card, fg_color="transparent")
        opts.pack(fill="x", padx=20, pady=8)
        self._upper  = ctk.BooleanVar(value=True)
        self._lower  = ctk.BooleanVar(value=True)
        self._digits = ctk.BooleanVar(value=True)
        self._symbols= ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(opts, text="Uppercase  (A-Z)", variable=self._upper).grid(row=0, column=0, sticky="w", padx=10, pady=4)
        ctk.CTkCheckBox(opts, text="Lowercase  (a-z)", variable=self._lower).grid(row=0, column=1, sticky="w", padx=10, pady=4)
        ctk.CTkCheckBox(opts, text="Digits  (0-9)",    variable=self._digits).grid(row=1, column=0, sticky="w", padx=10, pady=4)
        ctk.CTkCheckBox(opts, text="Symbols  (!@#…)",  variable=self._symbols).grid(row=1, column=1, sticky="w", padx=10, pady=4)

        self._no_ambiguous = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(card, text="Exclude ambiguous characters  (0 O l I 1)",
                        variable=self._no_ambiguous).pack(anchor="w", padx=20, pady=(4, 16))

        ctk.CTkButton(self, text="⚡  Generate Password", height=44,
                      font=ctk.CTkFont(size=14, weight="bold"),
                      command=self._generate).pack(pady=16, padx=40, fill="x")

        out_frame = ctk.CTkFrame(self, corner_radius=12)
        out_frame.pack(padx=40, pady=4, fill="x")
        out_frame.columnconfigure(0, weight=1)

        self._output = ctk.CTkEntry(out_frame, placeholder_text="Generated password appears here…",
                                    font=ctk.CTkFont(size=15, family="Courier"),
                                    height=46, state="readonly")
        self._output.grid(row=0, column=0, padx=(12, 4), pady=12, sticky="ew")
        ctk.CTkButton(out_frame, text="Copy", width=70,
                      command=self._copy).grid(row=0, column=1, padx=(4, 12), pady=12)

        self._strength_label = ctk.CTkLabel(self, text="", text_color="gray")
        self._strength_label.pack(pady=(4, 0))
        self._strength_bar = ctk.CTkProgressBar(self, height=8, corner_radius=4)
        self._strength_bar.set(0)
        self._strength_bar.pack(padx=40, fill="x", pady=(4, 20))


    def _on_length_change(self, value):
        self._length_label.configure(text=str(int(value)))

    def _build_charset(self):
        charset = ""
        if self._upper.get():  charset += string.ascii_uppercase
        if self._lower.get():  charset += string.ascii_lowercase
        if self._digits.get(): charset += string.digits
        if self._symbols.get():charset += string.punctuation
        if self._no_ambiguous.get():
            for ch in "0OlI1":
                charset = charset.replace(ch, "")
        return charset

    def _generate(self):
        charset = self._build_charset()
        if not charset:
            self._set_output("Select at least one character type.")
            return
        length = int(self._length_var.get())
        password = "".join(secrets.choice(charset) for _ in range(length))
        self._set_output(password)
        self._update_strength(password)

    def _set_output(self, text):
        self._output.configure(state="normal")
        self._output.delete(0, "end")
        self._output.insert(0, text)
        self._output.configure(state="readonly")

    def _copy(self):
        pwd = self._output.get()
        if pwd:
            self.clipboard_clear()
            self.clipboard_append(pwd)

    def _update_strength(self, password):
        score = 0
        length = len(password)
        if length >= 8:  score += 1
        if length >= 12: score += 1
        if length >= 16: score += 1
        if re.search(r"[A-Z]", password): score += 1
        if re.search(r"[a-z]", password): score += 1
        if re.search(r"\d",    password): score += 1
        if re.search(r"[^A-Za-z0-9]", password): score += 1

        ratio = score / 7
        self._strength_bar.set(ratio)

        if ratio < 0.43:
            label, color = "Weak", "#e05252"
        elif ratio < 0.72:
            label, color = "Moderate", "#e09b52"
        elif ratio < 0.90:
            label, color = "Strong", "#52a0e0"
        else:
            label, color = "Very Strong", "#52c07a"

        self._strength_label.configure(text=f"Strength: {label}", text_color=color)
        self._strength_bar.configure(progress_color=color)

class PasswordHealthTab(ctk.CTkFrame):

    COMMON_PASSWORDS = {
        "password", "123456", "12345678", "qwerty", "abc123", "monkey",
        "1234567", "letmein", "trustno1", "dragon", "baseball", "iloveyou",
        "master", "sunshine", "ashley", "bailey", "passw0rd", "shadow",
        "123123", "654321", "superman", "qazwsx", "michael", "football",
    }

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self._build_ui()

    def _build_ui(self):
        ctk.CTkLabel(self, text="Password Health Check",
                     font=ctk.CTkFont(size=22, weight="bold")).pack(pady=(20, 4))
        ctk.CTkLabel(self, text="Analyse any password for weaknesses before using it.",
                     text_color="gray").pack(pady=(0, 20))

        in_frame = ctk.CTkFrame(self, corner_radius=12)
        in_frame.pack(padx=40, pady=4, fill="x")
        in_frame.columnconfigure(0, weight=1)

        self._pw_var = ctk.StringVar()
        self._pw_entry = ctk.CTkEntry(in_frame, textvariable=self._pw_var,
                                      placeholder_text="Paste or type a password…",
                                      font=ctk.CTkFont(size=14, family="Courier"),
                                      height=44, show="•")
        self._pw_entry.grid(row=0, column=0, padx=(12, 4), pady=12, sticky="ew")

        self._show_var = ctk.BooleanVar(value=False)
        ctk.CTkButton(in_frame, text="Show", width=70,
                      command=self._toggle_show).grid(row=0, column=1, padx=(4, 4), pady=12)
        ctk.CTkButton(in_frame, text="Check", width=70,
                      command=self._check).grid(row=0, column=2, padx=(4, 12), pady=12)

        self._strength_label = ctk.CTkLabel(self, text="Strength: —", text_color="gray")
        self._strength_label.pack(pady=(10, 2))
        self._strength_bar = ctk.CTkProgressBar(self, height=10, corner_radius=5)
        self._strength_bar.set(0)
        self._strength_bar.pack(padx=40, fill="x", pady=(0, 16))

        self._results_frame = ctk.CTkScrollableFrame(self, corner_radius=12, height=240)
        self._results_frame.pack(padx=40, pady=4, fill="both", expand=True)

        self._pw_var.trace_add("write", lambda *_: self._live_strength())


    def _toggle_show(self):
        self._show_var.set(not self._show_var.get())
        self._pw_entry.configure(show="" if self._show_var.get() else "•")

    def _live_strength(self):
        pw = self._pw_var.get()
        if not pw:
            self._strength_bar.set(0)
            self._strength_label.configure(text="Strength: —", text_color="gray")
            return
        score, _ = self._score_password(pw)
        ratio = score / 7
        self._strength_bar.set(ratio)
        if ratio < 0.43:
            label, color = "Weak", "#e05252"
        elif ratio < 0.72:
            label, color = "Moderate", "#e09b52"
        elif ratio < 0.90:
            label, color = "Strong", "#52a0e0"
        else:
            label, color = "Very Strong", "#52c07a"
        self._strength_label.configure(text=f"Strength: {label}", text_color=color)
        self._strength_bar.configure(progress_color=color)

    def _score_password(self, pw):
        issues = []
        score = 0

        if len(pw) >= 8:  score += 1
        else: issues.append(("❌", "Too short, use at least 8 characters"))

        if len(pw) >= 12: score += 1
        else: issues.append(("⚠️", "Consider 12+ characters for better security"))

        if len(pw) >= 16: score += 1

        if re.search(r"[A-Z]", pw): score += 1
        else: issues.append(("❌", "No uppercase letters"))

        if re.search(r"[a-z]", pw): score += 1
        else: issues.append(("❌", "No lowercase letters"))

        if re.search(r"\d", pw): score += 1
        else: issues.append(("❌", "No digits"))

        if re.search(r"[^A-Za-z0-9]", pw): score += 1
        else: issues.append(("⚠️", "No special characters, add one for extra strength"))

        if pw.lower() in self.COMMON_PASSWORDS:
            score = max(0, score - 3)
            issues.insert(0, ("🚨", "This is a commonly used password , don't use it!"))

        if re.search(r"(.)\1{2,}", pw):
            issues.append(("⚠️", "Repeated characters detected (ex. 'aaa')"))

        if re.search(r"(012|123|234|345|456|567|678|789|890|abc|bcd|cde|qwe|wer)", pw.lower()):
            issues.append(("⚠️", "pattern detected (e.g. '123' or 'abc')"))

        if not issues:
            issues.append(("✅", "No issues found, this looks like a strong password!"))

        return score, issues

    def _check(self):
        pw = self._pw_var.get()
        for widget in self._results_frame.winfo_children():
            widget.destroy()

        if not pw:
            ctk.CTkLabel(self._results_frame, text="Please enter a password first.",
                         text_color="gray").pack(pady=20)
            return

        score, issues = self._score_password(pw)
        ratio = score / 7

        if ratio >= 0.90:
            banner_text, banner_color = "✅  Strong Password", "#52c07a"
        elif ratio >= 0.72:
            banner_text, banner_color = "🔵  Moderate Password", "#52a0e0"
        elif ratio >= 0.43:
            banner_text, banner_color = "⚠️  Weak Password", "#e09b52"
        else:
            banner_text, banner_color = "🚨  Very Weak Password", "#e05252"

        banner = ctk.CTkFrame(self._results_frame, fg_color=banner_color,
                              corner_radius=8)
        banner.pack(fill="x", padx=4, pady=(8, 4))
        ctk.CTkLabel(banner, text=banner_text,
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color="white").pack(pady=10)

        stats = ctk.CTkFrame(self._results_frame, corner_radius=8)
        stats.pack(fill="x", padx=4, pady=4)
        stats.columnconfigure((0, 1, 2), weight=1)

        has_upper   = bool(re.search(r"[A-Z]", pw))
        has_lower   = bool(re.search(r"[a-z]", pw))
        has_digit   = bool(re.search(r"\d", pw))
        has_symbol  = bool(re.search(r"[^A-Za-z0-9]", pw))
        entropy_bits = self._entropy(pw)

        def stat(col, label, value, good=True):
            color = "#52c07a" if good else "#e05252"
            f = ctk.CTkFrame(stats, fg_color="transparent")
            f.grid(row=0, column=col, padx=8, pady=8, sticky="ew")
            ctk.CTkLabel(f, text=value, font=ctk.CTkFont(size=16, weight="bold"),
                         text_color=color).pack()
            ctk.CTkLabel(f, text=label, text_color="gray",
                         font=ctk.CTkFont(size=11)).pack()

        stat(0, "Characters", str(len(pw)), len(pw) >= 12)
        stat(1, "Entropy (bits)", f"{entropy_bits:.1f}", entropy_bits >= 50)
        stat(2, "Character types",
             f"{'U' if has_upper else '—'}{'l' if has_lower else '—'}{'#' if has_digit else '—'}{'@' if has_symbol else '—'}",
             has_upper and has_lower and has_digit and has_symbol)

        ctk.CTkLabel(self._results_frame, text="Details",
                     font=ctk.CTkFont(size=13, weight="bold"),
                     anchor="w").pack(fill="x", padx=4, pady=(12, 4))

        for icon, msg in issues:
            row = ctk.CTkFrame(self._results_frame, corner_radius=6)
            row.pack(fill="x", padx=4, pady=2)
            ctk.CTkLabel(row, text=f"{icon}  {msg}",
                         anchor="w", wraplength=560).pack(fill="x", padx=12, pady=8)

    def _entropy(self, pw):
        pool = 0
        if re.search(r"[a-z]", pw): pool += 26
        if re.search(r"[A-Z]", pw): pool += 26
        if re.search(r"\d",    pw): pool += 10
        if re.search(r"[^A-Za-z0-9]", pw): pool += 32
        if pool == 0:
            return 0.0
        import math
        return len(pw) * math.log2(pool)
    
class I360VaultApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("I360 Vault - Password Manager")
        self.geometry("960x620")
        self.minsize(860, 540)
        self._vault_key = None
        self._frame     = None
        self._show_login()

    def _show_login(self):
        self._clear()
        from ui.login_screen import LoginScreen
        self._frame = LoginScreen(self, on_success=self._on_login)
        self._frame.pack(fill="both", expand=True)

    def _on_login(self, vault_key):
        self._vault_key = vault_key
        self._clear()
        from ui.dashboard_screen import DashboardScreen
        self._frame = DashboardScreen(self, vault_key=self._vault_key,
                                      on_logout=self._show_login)
        self._frame.pack(fill="both", expand=True)

    def _clear(self):
        if self._frame:
            self._frame.destroy()
            self._frame = None


if __name__ == "__main__":
    app = I360VaultApp()
    app.mainloop()
