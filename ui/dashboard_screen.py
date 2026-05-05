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
        self.parent    = parent
        self.vault_key = vault_key
        self.on_logout = on_logout
        self.all_entries   = []
        self._cb_timer = None
        self._build_ui()
        self._load()

    def _build_ui(self):
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

        # Add tabs for Passwords and SSH Keys
        self._tab_var = ctk.StringVar(value="passwords")
        tab_frame = ctk.CTkFrame(main, fg_color="transparent")
        tab_frame.pack(fill="x", pady=(10, 0))

        ctk.CTkButton(tab_frame, text="🔐 Passwords", height=36, width=120,
                      command=lambda: self._switch_tab("passwords")).pack(side="left", padx=4)
        ctk.CTkButton(tab_frame, text="🔑 SSH Keys", height=36, width=120,
                      command=lambda: self._switch_tab("ssh_keys")).pack(side="left", padx=4)

        self._status = ctk.CTkLabel(main, text="",
                                    font=ctk.CTkFont(size=12),
                                    text_color="#4caf7d")
        self._status.pack(fill="x", pady=(0, 6))

        self._entries_frame = ctk.CTkScrollableFrame(main)
        self._entries_frame.pack(fill="both", expand=True, pady=(10, 0))

    def _switch_tab(self, tab):
        self._tab_var.set(tab)
        for w in self._entries_frame.winfo_children():
            w.destroy()

        if tab == "ssh_keys":
            self._load_ssh_keys()
        else:
            self._load()

    def _load_ssh_keys(self):
        # Clear existing widgets
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
            self._status.configure(
                text="\U0001f512 Clipboard cleared.", text_color="gray")
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
        answer = messagebox.askyesno(
            "Delete", "Delete entry for " + site_name + "?")
        if answer:
            db.delete_entry(entry["id"])
            self._load()
            self._status.configure(
                text="Deleted entry for " + site_name + ".",
                text_color="gray")

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