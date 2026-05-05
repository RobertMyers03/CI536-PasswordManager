import customtkinter as ctk
import secrets, string, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import database as db
import crypto


class AddEntryScreen(ctk.CTkToplevel):
    def __init__(self, parent, vault_key, on_save, entry=None):
        super().__init__(parent)
        self.vault_key = vault_key
        self.on_save   = on_save
        self.entry     = entry
        self.title("Edit Password" if entry else "Add Password")
        self.geometry("460x550")
        self.resizable(False, False)
        self.grab_set()
        self.lift()
        self.focus_force()
        self._build_ui()

    def _build_ui(self):
        heading = "Edit Password" if self.entry else "Add New Password"
        ctk.CTkLabel(self, text=heading,
                     font=ctk.CTkFont(size=20, weight="bold")).pack(pady=(24, 4))

        form = ctk.CTkFrame(self, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=30, pady=8)

        ctk.CTkLabel(form, text="Website / App Name",
                     anchor="w", font=ctk.CTkFont(size=13)).pack(fill="x", pady=(10, 2))
        self._site = ctk.CTkEntry(form, placeholder_text="e.g. Google, Netflix", height=42)
        self._site.pack(fill="x")

        ctk.CTkLabel(form, text="Username or Email",
                     anchor="w", font=ctk.CTkFont(size=13)).pack(fill="x", pady=(14, 2))
        self._username = ctk.CTkEntry(form, placeholder_text="e.g. john@email.com", height=42)
        self._username.pack(fill="x")

        ctk.CTkLabel(form, text="Password",
                     anchor="w", font=ctk.CTkFont(size=13)).pack(fill="x", pady=(14, 2))

        pw_row = ctk.CTkFrame(form, fg_color="transparent")
        pw_row.pack(fill="x")

        self._pw = ctk.CTkEntry(pw_row, placeholder_text="Enter password",
                                show="\u2022", height=42)
        self._pw.pack(side="left", fill="x", expand=True, padx=(0, 6))

        self._show_pw = False
        ctk.CTkButton(pw_row, text="\U0001f441", width=46, height=42,
                      fg_color="transparent", border_width=1,
                      command=self._toggle).pack(side="right")

        ctk.CTkButton(form, text="\u26a1  Generate Strong Password",
                      height=36, fg_color="transparent", border_width=1,
                      font=ctk.CTkFont(size=12),
                      command=self._generate).pack(fill="x", pady=(8, 2))

        self._strength = ctk.CTkLabel(form, text="", font=ctk.CTkFont(size=12))
        self._strength.pack(pady=2)

        self._error = ctk.CTkLabel(form, text="", text_color="#e05252",
                                   font=ctk.CTkFont(size=12))
        self._error.pack()

        btn_row = ctk.CTkFrame(form, fg_color="transparent")
        btn_row.pack(fill="x", pady=14)

        ctk.CTkButton(btn_row, text="Cancel", width=100,
                      fg_color="transparent", border_width=1,
                      command=self.destroy).pack(side="left", padx=(0, 10))

        ctk.CTkButton(btn_row, text="\U0001f4be  Save",
                      height=42, font=ctk.CTkFont(size=14, weight="bold"),
                      command=self._save).pack(side="right", fill="x", expand=True)

        if self.entry:
            self._site.insert(0, self.entry["site"])
            self._username.insert(0, self.entry["username"])
            self._pw.insert(0, self.entry["password"])
            self._check_strength()

        self._pw.bind("<KeyRelease>", lambda _: self._check_strength())

    def _toggle(self):
        self._show_pw = not self._show_pw
        self._pw.configure(show="" if self._show_pw else "\u2022")

    def _generate(self):
        chars = string.ascii_letters + string.digits + "!@#$%^&*"
        pwd = "".join(secrets.choice(chars) for _ in range(20))
        self._pw.delete(0, "end")
        self._pw.configure(show="")
        self._pw.insert(0, pwd)
        self._show_pw = True
        self._check_strength()

    def _check_strength(self):
        pw = self._pw.get()
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

    def _save(self):
        site     = self._site.get().strip()
        username = self._username.get().strip()
        password = self._pw.get()

        if not site:
            self._error.configure(text="Please enter a website or app name.")
            return
        if not username:
            self._error.configure(text="Please enter a username or email.")
            return
        if not password:
            self._error.configure(text="Please enter a password.")
            return

        nonce, ciphertext = crypto.encrypt_password(password, self.vault_key)
        if self.entry:
            db.update_entry(self.entry["id"], site, username, nonce, ciphertext)
        else:
            db.add_entry(site, username, nonce, ciphertext)

        self.on_save()
        self.destroy()