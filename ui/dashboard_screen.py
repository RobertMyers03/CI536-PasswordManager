import customtkinter as ctk
from tkinter import messagebox
import threading, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import database as db
import crypto


def _clipboard_copy(widget, text):
    try:
        import pyperclip
        pyperclip.copy(text)
    except Exception:
        widget.clipboard_clear()
        widget.clipboard_append(text)
        widget.update()


def _clipboard_clear(widget):
    try:
        import pyperclip
        pyperclip.copy("")
    except Exception:
        try:
            widget.clipboard_clear()
            widget.update()
        except Exception:
            pass


class DashboardScreen(ctk.CTkFrame):
    def __init__(self, parent, vault_key, on_logout):
        super().__init__(parent, fg_color="transparent")
        self.parent      = parent
        self.vault_key   = vault_key
        self.on_logout   = on_logout
        self.all_entries = []
        self._cb_timer   = None
        self._build_ui()
        self._load()

    def _build_ui(self):
        # ── Sidebar ───────────────────────────────────────────────────────────
        sidebar = ctk.CTkFrame(self, width=210, corner_radius=0)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        ctk.CTkLabel(sidebar, text="\U0001f510 SecureVault",
                     font=ctk.CTkFont(size=18, weight="bold")).pack(
                         pady=(30, 20), padx=15)

        ctk.CTkButton(sidebar, text="+  Add Password",
                      height=42, font=ctk.CTkFont(size=13),
                      command=self._add).pack(padx=15, pady=4, fill="x")

        ctk.CTkButton(sidebar, text="+  Add SSH Key",
                      height=42, font=ctk.CTkFont(size=13),
                      command=self._add_ssh_key).pack(padx=15, pady=4, fill="x")

        ctk.CTkLabel(sidebar, text="").pack(expand=True)

        ctk.CTkButton(sidebar, text="\U0001f512  Lock Vault",
                      height=40, font=ctk.CTkFont(size=13),
                      fg_color="transparent", border_width=1,
                      command=self._logout).pack(padx=15, pady=20, fill="x")

        # ── Main area ─────────────────────────────────────────────────────────
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.pack(side="right", fill="both", expand=True, padx=20, pady=20)

        hdr = ctk.CTkFrame(main, fg_color="transparent")
        hdr.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(hdr, text="Your Passwords",
                     font=ctk.CTkFont(size=22, weight="bold")).pack(side="left")

        self._search_var = ctk.StringVar()
        self._search_var.trace("w", self._on_search)
        ctk.CTkEntry(hdr, placeholder_text="Search...",
                     textvariable=self._search_var,
                     width=240, height=38).pack(side="right")

        # ── Tab buttons row ───────────────────────────────────────────────────
        self._tab_var = ctk.StringVar(value="passwords")
        tab_frame = ctk.CTkFrame(main, fg_color="transparent")
        tab_frame.pack(fill="x", pady=(10, 0))

        self._tab_btns = {}
        tabs = [
            ("passwords",  "\U0001f510 Passwords"),
            ("ssh_keys",   "\U0001f511 SSH Keys"),
            ("generator",  "\u26a1 Generator"),
            ("health",     "\U0001fa7a Health Check"),
        ]
        for key, label in tabs:
            btn = ctk.CTkButton(tab_frame, text=label, height=36, width=120,
                                command=lambda k=key: self._switch_tab(k))
            btn.pack(side="left", padx=4)
            self._tab_btns[key] = btn

        self._status = ctk.CTkLabel(main, text="",
                                    font=ctk.CTkFont(size=12),
                                    text_color="#4caf7d")
        self._status.pack(fill="x", pady=(6, 0))

        self._entries_frame = ctk.CTkScrollableFrame(main)
        self._entries_frame.pack(fill="both", expand=True, pady=(10, 0))

    # ── Tab switching ─────────────────────────────────────────────────────────

    def _switch_tab(self, tab):
        self._tab_var.set(tab)
        for w in self._entries_frame.winfo_children():
            w.destroy()
        if tab == "ssh_keys":
            self._load_ssh_keys()
        elif tab == "generator":
            self._show_generator()
        elif tab == "health":
            self._show_health()
        else:
            self._load()

    # ── Generator tab content ─────────────────────────────────────────────────

    def _show_generator(self):
        import secrets, string, re

        form = ctk.CTkFrame(self._entries_frame, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=10, pady=8)

        ctk.CTkLabel(form, text="Password Generator",
                     font=ctk.CTkFont(size=20, weight="bold")).pack(pady=(10, 4))

        # Length
        length_row = ctk.CTkFrame(form, fg_color="transparent")
        length_row.pack(fill="x", pady=(10, 2))
        ctk.CTkLabel(length_row, text="Password Length",
                     anchor="w", font=ctk.CTkFont(size=13)).pack(side="left")
        length_label = ctk.CTkLabel(length_row, text="16",
                                    font=ctk.CTkFont(size=13, weight="bold"))
        length_label.pack(side="right")

        length_var = ctk.IntVar(value=16)

        def on_length(v):
            length_label.configure(text=str(int(float(v))))

        ctk.CTkSlider(form, from_=8, to=64, number_of_steps=56,
                      variable=length_var,
                      command=on_length).pack(fill="x", pady=(4, 10))

        # Checkboxes
        ctk.CTkLabel(form, text="Include Characters",
                     anchor="w", font=ctk.CTkFont(size=13)).pack(fill="x", pady=(4, 6))

        opts = ctk.CTkFrame(form, fg_color="transparent")
        opts.pack(fill="x")
        opts.columnconfigure((0, 1), weight=1)

        upper   = ctk.BooleanVar(value=True)
        lower   = ctk.BooleanVar(value=True)
        digits  = ctk.BooleanVar(value=True)
        symbols = ctk.BooleanVar(value=True)
        no_ambig= ctk.BooleanVar(value=False)

        ctk.CTkCheckBox(opts, text="Uppercase  (A-Z)", variable=upper).grid(row=0, column=0, sticky="w", pady=3)
        ctk.CTkCheckBox(opts, text="Lowercase  (a-z)", variable=lower).grid(row=0, column=1, sticky="w", pady=3)
        ctk.CTkCheckBox(opts, text="Digits  (0-9)",    variable=digits).grid(row=1, column=0, sticky="w", pady=3)
        ctk.CTkCheckBox(opts, text="Symbols  (!@#…)",  variable=symbols).grid(row=1, column=1, sticky="w", pady=3)
        ctk.CTkCheckBox(opts, text="Exclude ambiguous characters  (0 O l I 1)",
                        variable=no_ambig).grid(row=2, column=0, columnspan=2, sticky="w", pady=3)

        strength_lbl = ctk.CTkLabel(form, text="", font=ctk.CTkFont(size=12))

        # Output row
        ctk.CTkLabel(form, text="Generated Password",
                     anchor="w", font=ctk.CTkFont(size=13)).pack(fill="x", pady=(14, 2))

        pw_row = ctk.CTkFrame(form, fg_color="transparent")
        pw_row.pack(fill="x")

        output = ctk.CTkEntry(pw_row, placeholder_text="Password appears here\u2026",
                              font=ctk.CTkFont(size=13, family="Courier"),
                              height=42, state="readonly")
        output.pack(side="left", fill="x", expand=True, padx=(0, 6))

        ctk.CTkButton(pw_row, text="Copy", width=80, height=42,
                      fg_color="transparent", border_width=1,
                      command=lambda: (
                          self.clipboard_clear(),
                          self.clipboard_append(output.get())
                      )).pack(side="right")

        def set_output(text):
            output.configure(state="normal")
            output.delete(0, "end")
            output.insert(0, text)
            output.configure(state="readonly")

        def check_strength(pw):
            score = sum([len(pw) >= 8, len(pw) >= 14,
                         any(c.isupper() for c in pw), any(c.islower() for c in pw),
                         any(c.isdigit() for c in pw),
                         any(c in "!@#$%^&*()_+-=" for c in pw)])
            if score <= 2:
                strength_lbl.configure(text="Strength: Weak \u274c", text_color="#e05252")
            elif score <= 4:
                strength_lbl.configure(text="Strength: Medium \u26a0\ufe0f", text_color="orange")
            else:
                strength_lbl.configure(text="Strength: Strong \u2705", text_color="#4caf7d")

        def generate():
            charset = ""
            if upper.get():   charset += string.ascii_uppercase
            if lower.get():   charset += string.ascii_lowercase
            if digits.get():  charset += string.digits
            if symbols.get(): charset += "!@#$%^&*()_+-=[]{}|;:,.<>?"
            if no_ambig.get():
                for ch in "0OlI1":
                    charset = charset.replace(ch, "")
            if not charset:
                strength_lbl.configure(text="Select at least one character type.", text_color="#e05252")
                return
            pw = "".join(secrets.choice(charset) for _ in range(int(length_var.get())))
            set_output(pw)
            check_strength(pw)

        ctk.CTkButton(form, text="\u26a1  Generate Strong Password",
                      height=36, fg_color="transparent", border_width=1,
                      font=ctk.CTkFont(size=12),
                      command=generate).pack(fill="x", pady=(14, 6))

        strength_lbl.pack(pady=(4, 2))

    # ── Health Check tab content ──────────────────────────────────────────────

    def _show_health(self):
        import re, math

        COMMON = {
            "password", "123456", "12345678", "qwerty", "abc123", "monkey",
            "1234567", "letmein", "trustno1", "dragon", "baseball", "iloveyou",
            "master", "sunshine", "ashley", "bailey", "passw0rd", "shadow",
            "123123", "654321", "superman", "qazwsx", "michael", "football",
        }

        form = ctk.CTkFrame(self._entries_frame, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=10, pady=8)

        ctk.CTkLabel(form, text="Password Health Check",
                     font=ctk.CTkFont(size=20, weight="bold")).pack(pady=(10, 4))

        ctk.CTkLabel(form, text="Password to Check",
                     anchor="w", font=ctk.CTkFont(size=13)).pack(fill="x", pady=(10, 2))

        pw_row = ctk.CTkFrame(form, fg_color="transparent")
        pw_row.pack(fill="x")

        pw_var  = ctk.StringVar()
        show_pw = [False]

        pw_entry = ctk.CTkEntry(pw_row, textvariable=pw_var,
                                placeholder_text="Paste or type a password\u2026",
                                show="\u2022", height=42)
        pw_entry.pack(side="left", fill="x", expand=True, padx=(0, 6))

        def toggle():
            show_pw[0] = not show_pw[0]
            pw_entry.configure(show="" if show_pw[0] else "\u2022")

        ctk.CTkButton(pw_row, text="\U0001f441", width=46, height=42,
                      fg_color="transparent", border_width=1,
                      command=toggle).pack(side="right")

        strength_lbl = ctk.CTkLabel(form, text="", font=ctk.CTkFont(size=12))
        strength_lbl.pack(pady=(6, 2))

        results_frame = ctk.CTkFrame(form, fg_color="transparent")

        def live_strength(*_):
            pw = pw_var.get()
            if not pw:
                strength_lbl.configure(text="", text_color="gray")
                return
            score = sum([len(pw) >= 8, len(pw) >= 14,
                         any(c.isupper() for c in pw), any(c.islower() for c in pw),
                         any(c.isdigit() for c in pw),
                         any(c in "!@#$%^&*()_+-=" for c in pw)])
            if score <= 2:
                strength_lbl.configure(text="Strength: Weak \u274c", text_color="#e05252")
            elif score <= 4:
                strength_lbl.configure(text="Strength: Medium \u26a0\ufe0f", text_color="orange")
            else:
                strength_lbl.configure(text="Strength: Strong \u2705", text_color="#4caf7d")

        pw_var.trace_add("write", live_strength)

        def check():
            for w in results_frame.winfo_children():
                w.destroy()
            results_frame.pack(fill="x", pady=(4, 0))

            pw = pw_var.get()
            if not pw:
                ctk.CTkLabel(results_frame, text="Please enter a password first.",
                             text_color="#e05252", font=ctk.CTkFont(size=12),
                             anchor="w").pack(fill="x", pady=2)
                return

            issues = []

            if len(pw) < 8:
                issues.append(("\u274c", "Too short — use at least 8 characters.", "#e05252"))
            elif len(pw) < 14:
                issues.append(("\u26a0\ufe0f", f"Consider 14+ characters (currently {len(pw)}).", "orange"))
            else:
                issues.append(("\u2705", f"Good length ({len(pw)} characters).", "#4caf7d"))

            checks = [
                (any(c.isupper() for c in pw), "Contains uppercase letters.", "No uppercase letters."),
                (any(c.islower() for c in pw), "Contains lowercase letters.", "No lowercase letters."),
                (any(c.isdigit() for c in pw), "Contains digits.",            "No digits."),
                (any(c in "!@#$%^&*()_+-=" for c in pw),
                 "Contains special characters.",
                 "No special characters — add one for extra strength."),
            ]
            for ok, good_msg, bad_msg in checks:
                if ok:
                    issues.append(("\u2705", good_msg, "#4caf7d"))
                else:
                    issues.append(("\u274c" if "digits" in bad_msg or "upper" in bad_msg or "lower" in bad_msg
                                   else "\u26a0\ufe0f", bad_msg,
                                   "#e05252" if "digits" in bad_msg or "upper" in bad_msg or "lower" in bad_msg
                                   else "orange"))

            if pw.lower() in COMMON:
                issues.insert(0, ("\U0001f6a8", "Commonly-used password — do not use it!", "#e05252"))

            if re.search(r"(.)\1{2,}", pw):
                issues.append(("\u26a0\ufe0f", "Repeated characters detected (e.g. \'aaa\').", "orange"))

            if re.search(r"(012|123|234|345|456|567|678|789|890|abc|bcd|cde|qwe|wer)", pw.lower()):
                issues.append(("\u26a0\ufe0f", "Sequential pattern detected (e.g. \'123\' or \'abc\').", "orange"))

            pool = sum([26 if re.search(r"[a-z]", pw) else 0,
                        26 if re.search(r"[A-Z]", pw) else 0,
                        10 if re.search(r"\d", pw) else 0,
                        32 if re.search(r"[^A-Za-z0-9]", pw) else 0])
            entropy = len(pw) * math.log2(pool) if pool else 0
            ent_icon  = "\u2705" if entropy >= 50 else ("\u26a0\ufe0f" if entropy >= 30 else "\u274c")
            ent_color = "#4caf7d" if entropy >= 50 else ("orange" if entropy >= 30 else "#e05252")
            issues.append((ent_icon, f"Estimated entropy: {entropy:.0f} bits.", ent_color))

            for icon, msg, color in issues:
                ctk.CTkLabel(results_frame, text=f"{icon}  {msg}",
                             anchor="w", font=ctk.CTkFont(size=12),
                             text_color=color).pack(fill="x", pady=2)

        ctk.CTkButton(form, text="\U0001fa7a  Check Password",
                      height=42, font=ctk.CTkFont(size=14, weight="bold"),
                      command=check).pack(fill="x", pady=(6, 10))

        results_frame.pack(fill="x", pady=(4, 0))

    # ── SSH Keys ──────────────────────────────────────────────────────────────

    def _load_ssh_keys(self):
        for w in self._entries_frame.winfo_children():
            w.destroy()
        self._all_keys = db.get_all_ssh_keys()
        if not self._all_keys:
            ctk.CTkLabel(
                self._entries_frame,
                text="No SSH keys saved yet.\n\nClick  + Add SSH Key  to get started.",
                font=ctk.CTkFont(size=14), text_color="gray").pack(pady=60)
            return
        for key_id, name, public_key, nonce, ciphertext in self._all_keys:
            self._display_ssh_key(key_id, name, public_key, nonce, ciphertext)

    def _display_ssh_key(self, key_id, name, public_key, nonce, ciphertext):
        card = ctk.CTkFrame(self._entries_frame, corner_radius=8, border_width=1, border_color="#444")
        card.pack(fill="x", pady=6, padx=2)

        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(side="left", fill="both", expand=True, padx=12, pady=10)

        ctk.CTkLabel(content, text=name, font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w")
        pub_preview = (public_key[:50] + "...") if len(public_key) > 50 else public_key
        ctk.CTkLabel(content, text=pub_preview,
                     text_color="gray", font=ctk.CTkFont(size=11)).pack(anchor="w", pady=(4, 0))

        buttons = ctk.CTkFrame(card, fg_color="transparent")
        buttons.pack(side="right", padx=8, pady=8)

        ctk.CTkButton(buttons, text="Edit", width=60, height=32,
                      command=lambda: self._edit_ssh_key(key_id)).pack(side="left", padx=2)
        ctk.CTkButton(buttons, text="Delete", width=60, height=32, fg_color="#ff3b3b",
                      command=lambda: self._delete_ssh_key(key_id)).pack(side="left", padx=2)

    def _edit_ssh_key(self, key_id):
        from ui.add_ssh_key_screen import AddSSHKeyScreen
        entry = next((e for e in self._all_keys if e[0] == key_id), None)
        if entry:
            AddSSHKeyScreen(self.parent, self.vault_key, self._load_ssh_keys, entry=entry)

    def _delete_ssh_key(self, key_id):
        if messagebox.askyesno("Confirm", "Delete this SSH key?"):
            db.delete_ssh_key(key_id)
            self._load_ssh_keys()

    # ── Passwords ─────────────────────────────────────────────────────────────

    def _load(self):
        self.all_entries = []
        for row in db.get_all_entries():
            eid, site, username, nonce, ct = row
            try:
                pw = crypto.decrypt_password(nonce, ct, self.vault_key)
                self.all_entries.append({
                    "id": eid, "site": site,
                    "username": username, "password": pw
                })
            except Exception:
                pass
        self._render(self.all_entries)

    def _render(self, entries):
        for w in self._entries_frame.winfo_children():
            w.destroy()
        if not entries:
            ctk.CTkLabel(
                self._entries_frame,
                text="No passwords saved yet.\n\nClick  + Add Password  to get started.",
                font=ctk.CTkFont(size=14), text_color="gray").pack(pady=60)
            return
        for e in entries:
            self._card(e)

    def _card(self, entry):
        card = ctk.CTkFrame(self._entries_frame)
        card.pack(fill="x", pady=4, padx=2)

        info = ctk.CTkFrame(card, fg_color="transparent")
        info.pack(side="left", fill="both", expand=True, padx=14, pady=12)

        ctk.CTkLabel(info, text=entry["site"],
                     font=ctk.CTkFont(size=15, weight="bold"),
                     anchor="w").pack(fill="x")
        ctk.CTkLabel(info, text=entry["username"],
                     font=ctk.CTkFont(size=12),
                     text_color="gray", anchor="w").pack(fill="x")

        btns = ctk.CTkFrame(card, fg_color="transparent")
        btns.pack(side="right", padx=10, pady=10)

        ctk.CTkButton(btns, text="Copy", width=80, height=32,
                      font=ctk.CTkFont(size=12),
                      command=lambda e=entry: self._copy(e["password"])
                      ).pack(side="left", padx=2)
        ctk.CTkButton(btns, text="Edit", width=72, height=32,
                      font=ctk.CTkFont(size=12),
                      fg_color="transparent", border_width=1,
                      command=lambda e=entry: self._edit(e)
                      ).pack(side="left", padx=2)
        ctk.CTkButton(btns, text="Delete", width=70, height=32,
                      font=ctk.CTkFont(size=12),
                      fg_color="transparent", border_width=1,
                      text_color="#e05252", border_color="#e05252",
                      command=lambda e=entry: self._delete(e)
                      ).pack(side="left", padx=2)

    def _copy(self, password):
        _clipboard_copy(self.parent, password)
        self._status.configure(
            text="Copied! Clipboard clears automatically in 30 seconds.",
            text_color="#4caf7d")
        if self._cb_timer:
            self._cb_timer.cancel()
        self._cb_timer = threading.Timer(30.0, self._auto_clear)
        self._cb_timer.daemon = True
        self._cb_timer.start()

    def _auto_clear(self):
        _clipboard_clear(self.parent)
        try:
            self._status.configure(text="\U0001f512 Clipboard cleared.", text_color="gray")
        except Exception:
            pass

    def _on_search(self, *_):
        q = self._search_var.get().lower()
        self._render([e for e in self.all_entries
                      if q in e["site"].lower() or q in e["username"].lower()])

    def _add(self):
        from ui.add_entry_screen import AddEntryScreen
        AddEntryScreen(self.parent, vault_key=self.vault_key, on_save=self._load)

    def _edit(self, entry):
        from ui.add_entry_screen import AddEntryScreen
        AddEntryScreen(self.parent, vault_key=self.vault_key,
                       on_save=self._load, entry=entry)

    def _delete(self, entry):
        site_name = entry["site"]
        if messagebox.askyesno("Delete", "Delete entry for " + site_name + "?"):
            db.delete_entry(entry["id"])
            self._load()
            self._status.configure(text="Deleted entry for " + site_name + ".", text_color="gray")

    def _logout(self):
        self.vault_key = None
        if self._cb_timer:
            self._cb_timer.cancel()
        _clipboard_clear(self.parent)
        self.on_logout()

    def _add_ssh_key(self):
        from ui.add_ssh_key_screen import AddSSHKeyScreen
        def on_save_ssh():
            self._switch_tab("ssh_keys")
        AddSSHKeyScreen(self.parent, self.vault_key, on_save_ssh)
