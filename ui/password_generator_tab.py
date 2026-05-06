import customtkinter as ctk
import secrets, string, re


class PasswordGeneratorTab(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self._build_ui()

    def _build_ui(self):
        ctk.CTkLabel(self, text="Password Generator",
                     font=ctk.CTkFont(size=20, weight="bold")).pack(pady=(24, 4))

        form = ctk.CTkFrame(self, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=30, pady=8)
 
        length_row = ctk.CTkFrame(form, fg_color="transparent")
        length_row.pack(fill="x", pady=(10, 2))
        ctk.CTkLabel(length_row, text="Password Length",
                     anchor="w", font=ctk.CTkFont(size=13)).pack(side="left")
        self._length_label = ctk.CTkLabel(length_row, text="16",
                                          font=ctk.CTkFont(size=13, weight="bold"))
        self._length_label.pack(side="right")

        self._length_var = ctk.IntVar(value=16)
        ctk.CTkSlider(form, from_=8, to=64, number_of_steps=56,
                      variable=self._length_var,
                      command=self._on_length_change).pack(fill="x", pady=(4, 10))

        ctk.CTkLabel(form, text="Include Characters",
                     anchor="w", font=ctk.CTkFont(size=13)).pack(fill="x", pady=(4, 6))

        opts = ctk.CTkFrame(form, fg_color="transparent")
        opts.pack(fill="x")
        opts.columnconfigure((0, 1), weight=1)

        self._upper      = ctk.BooleanVar(value=True)
        self._lower      = ctk.BooleanVar(value=True)
        self._digits     = ctk.BooleanVar(value=True)
        self._symbols    = ctk.BooleanVar(value=True)
        self._no_ambig   = ctk.BooleanVar(value=False)

        ctk.CTkCheckBox(opts, text="Uppercase  (A-Z)",  variable=self._upper).grid(row=0, column=0, sticky="w", pady=3)
        ctk.CTkCheckBox(opts, text="Lowercase  (a-z)",  variable=self._lower).grid(row=0, column=1, sticky="w", pady=3)
        ctk.CTkCheckBox(opts, text="Digits  (0-9)",     variable=self._digits).grid(row=1, column=0, sticky="w", pady=3)
        ctk.CTkCheckBox(opts, text="Symbols  (!@#…)",   variable=self._symbols).grid(row=1, column=1, sticky="w", pady=3)
        ctk.CTkCheckBox(opts, text="Exclude ambiguous characters  (0 O l I 1)",
                        variable=self._no_ambig).grid(row=2, column=0, columnspan=2, sticky="w", pady=3)

        ctk.CTkButton(form, text="\u26a1  Generate Strong Password",
                      height=36, fg_color="transparent", border_width=1,
                      font=ctk.CTkFont(size=12),
                      command=self._generate).pack(fill="x", pady=(14, 6))

        ctk.CTkLabel(form, text="Generated Password",
                     anchor="w", font=ctk.CTkFont(size=13)).pack(fill="x", pady=(10, 2))

        pw_row = ctk.CTkFrame(form, fg_color="transparent")
        pw_row.pack(fill="x")

        self._output = ctk.CTkEntry(pw_row, placeholder_text="Password appears here…",
                                    font=ctk.CTkFont(size=13, family="Courier"),
                                    height=42, state="readonly")
        self._output.pack(side="left", fill="x", expand=True, padx=(0, 6))

        ctk.CTkButton(pw_row, text="Copy", width=80, height=42,
                      fg_color="transparent", border_width=1,
                      command=self._copy).pack(side="right")

        self._strength = ctk.CTkLabel(form, text="", font=ctk.CTkFont(size=12))
        self._strength.pack(pady=(6, 2))

    def _on_length_change(self, value):
        self._length_label.configure(text=str(int(value)))

    def _build_charset(self):
        charset = ""
        if self._upper.get():   charset += string.ascii_uppercase
        if self._lower.get():   charset += string.ascii_lowercase
        if self._digits.get():  charset += string.digits
        if self._symbols.get(): charset += "!@#$%^&*()_+-=[]{}|;:,.<>?"
        if self._no_ambig.get():
            for ch in "0OlI1":
                charset = charset.replace(ch, "")
        return charset

    def _generate(self):
        charset = self._build_charset()
        if not charset:
            self._strength.configure(text="Select at least one character type.", text_color="#e05252")
            return
        length = int(self._length_var.get())
        password = "".join(secrets.choice(charset) for _ in range(length))
        self._set_output(password)
        self._check_strength(password)

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

    def _check_strength(self, pw):
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
