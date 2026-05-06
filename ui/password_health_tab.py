import customtkinter as ctk
import re, math


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
                     font=ctk.CTkFont(size=20, weight="bold")).pack(pady=(24, 4))

        form = ctk.CTkFrame(self, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=30, pady=8)

        ctk.CTkLabel(form, text="Password to Check",
                     anchor="w", font=ctk.CTkFont(size=13)).pack(fill="x", pady=(10, 2))

        pw_row = ctk.CTkFrame(form, fg_color="transparent")
        pw_row.pack(fill="x")

        self._pw_var = ctk.StringVar()
        self._pw_entry = ctk.CTkEntry(pw_row, textvariable=self._pw_var,
                                      placeholder_text="Paste or type a password…",
                                      show="\u2022", height=42)
        self._pw_entry.pack(side="left", fill="x", expand=True, padx=(0, 6))

        self._show_pw = False
        ctk.CTkButton(pw_row, text="\U0001f441", width=46, height=42,
                      fg_color="transparent", border_width=1,
                      command=self._toggle).pack(side="right")

        self._strength = ctk.CTkLabel(form, text="", font=ctk.CTkFont(size=12))
        self._strength.pack(pady=(6, 2))

        ctk.CTkButton(form, text="\U0001fa7a  Check Password",
                      height=42, font=ctk.CTkFont(size=14, weight="bold"),
                      command=self._check).pack(fill="x", pady=(6, 10))

        self._results = ctk.CTkScrollableFrame(form, fg_color="transparent")
        self._results.pack(fill="both", expand=True, pady=(4, 0))

        self._pw_var.trace_add("write", lambda *_: self._live_strength())


    def _toggle(self):
        self._show_pw = not self._show_pw
        self._pw_entry.configure(show="" if self._show_pw else "\u2022")

    def _live_strength(self):
        pw = self._pw_var.get()
        if not pw:
            self._strength.configure(text="", text_color="gray")
            return
        score = sum([len(pw) >= 8, len(pw) >= 14,
                     any(c.isupper() for c in pw), any(c.islower() for c in pw),
                     any(c.isdigit() for c in pw),
                     any(c in "!@#$%^&*()_+-=" for c in pw)])
        if score <= 2:
            self._strength.configure(text="Strength: Weak \u274c", text_color="#e05252")
        elif score <= 4:
            self._strength.configure(text="Strength: Medium \u26a0\ufe0f", text_color="orange")
        else:
            self._strength.configure(text="Strength: Strong \u2705", text_color="#4caf7d")

    def _check(self):
        for w in self._results.winfo_children():
            w.destroy()

        pw = self._pw_var.get()
        if not pw:
            self._error("Please enter a password first.")
            return

        issues = []

        if len(pw) < 8:
            issues.append(("\u274c", "Too short — use at least 8 characters.", "#e05252"))
        elif len(pw) < 14:
            issues.append(("\u26a0\ufe0f", "Consider 14+ characters for better security.", "orange"))
        else:
            issues.append(("\u2705", f"Good length ({len(pw)} characters).", "#4caf7d"))

        if not any(c.isupper() for c in pw):
            issues.append(("\u274c", "No uppercase letters.", "#e05252"))
        else:
            issues.append(("\u2705", "Contains uppercase letters.", "#4caf7d"))

        if not any(c.islower() for c in pw):
            issues.append(("\u274c", "No lowercase letters.", "#e05252"))
        else:
            issues.append(("\u2705", "Contains lowercase letters.", "#4caf7d"))

        if not any(c.isdigit() for c in pw):
            issues.append(("\u274c", "No digits.", "#e05252"))
        else:
            issues.append(("\u2705", "Contains digits.", "#4caf7d"))

        if not any(c in "!@#$%^&*()_+-=" for c in pw):
            issues.append(("\u26a0\ufe0f", "No special characters — add one for extra strength.", "orange"))
        else:
            issues.append(("\u2705", "Contains special characters.", "#4caf7d"))

        if pw.lower() in self.COMMON_PASSWORDS:
            issues.insert(0, ("\U0001f6a8", "This is a commonly-used password — do not use it!", "#e05252"))

        if re.search(r"(.)\1{2,}", pw):
            issues.append(("\u26a0\ufe0f", "Repeated characters detected (e.g. \'aaa\').", "orange"))

        if re.search(r"(012|123|234|345|456|567|678|789|890|abc|bcd|cde|qwe|wer)", pw.lower()):
            issues.append(("\u26a0\ufe0f", "Sequential pattern detected (e.g. \'123\' or \'abc\').", "orange"))

        pool = sum([26 if re.search(r"[a-z]", pw) else 0,
                    26 if re.search(r"[A-Z]", pw) else 0,
                    10 if re.search(r"\d",    pw) else 0,
                    32 if re.search(r"[^A-Za-z0-9]", pw) else 0])
        entropy = len(pw) * math.log2(pool) if pool else 0

        ent_label = f"Estimated entropy: {entropy:.0f} bits"
        ent_color = "#4caf7d" if entropy >= 50 else ("orange" if entropy >= 30 else "#e05252")
        ent_icon  = "\u2705" if entropy >= 50 else ("\u26a0\ufe0f" if entropy >= 30 else "\u274c")
        issues.append((ent_icon, ent_label, ent_color))

        for icon, msg, color in issues:
            ctk.CTkLabel(self._results, text=f"{icon}  {msg}",
                         anchor="w", font=ctk.CTkFont(size=12),
                         text_color=color).pack(fill="x", pady=2)

    def _error(self, msg):
        ctk.CTkLabel(self._results, text=msg, text_color="#e05252",
                     font=ctk.CTkFont(size=12), anchor="w").pack(fill="x", pady=2)
