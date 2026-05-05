import customtkinter as ctk
from tkinter import messagebox, filedialog
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import database as db
import crypto


class AddSSHKeyScreen(ctk.CTkToplevel):
    def __init__(self, parent, vault_key, on_save, entry=None):
        super().__init__(parent)
        self.vault_key = vault_key
        self.on_save   = on_save
        self.entry     = entry
        self.title("Edit SSH Key" if entry else "Add SSH Key")
        self.geometry("520x650")
        self.resizable(False, False)
        self.grab_set()
        self.lift()
        self.focus_force()
        self._build_ui()
        if entry:
            self._load_entry()

    def _build_ui(self):
        heading = "Edit SSH Key" if self.entry else "Add New SSH Key"
        ctk.CTkLabel(self, text=heading,
                     font=ctk.CTkFont(size=20, weight="bold")).pack(pady=(24, 4))

        form = ctk.CTkFrame(self, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=30, pady=8)

        ctk.CTkLabel(form, text="Key Name",
                     anchor="w", font=ctk.CTkFont(size=13)).pack(fill="x", pady=(10, 2))
        self._name = ctk.CTkEntry(form, placeholder_text="e.g. GitHub SSH Key", height=42)
        self._name.pack(fill="x")

        ctk.CTkLabel(form, text="Public Key",
                     anchor="w", font=ctk.CTkFont(size=13)).pack(fill="x", pady=(14, 2))
        self._public = ctk.CTkTextbox(form, height=100, wrap="word")
        self._public.pack(fill="x")

        ctk.CTkButton(form, text="Load from File",
                      height=36, fg_color="transparent", border_width=1,
                      font=ctk.CTkFont(size=12),
                      command=self._load_public_file).pack(fill="x", pady=(8, 2))

        ctk.CTkLabel(form, text="Private Key (Encrypted)",
                     anchor="w", font=ctk.CTkFont(size=13)).pack(fill="x", pady=(14, 2))
        self._private = ctk.CTkTextbox(form, height=150, wrap="word")
        self._private.pack(fill="x")

        ctk.CTkButton(form, text="Load from File",
                      height=36, fg_color="transparent", border_width=1,
                      font=ctk.CTkFont(size=12),
                      command=self._load_private_file).pack(fill="x", pady=(8, 2))

        btn_frame = ctk.CTkFrame(form, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(20, 0))

        ctk.CTkButton(btn_frame, text="Save", height=40,
                      command=self._save).pack(side="left", fill="x", expand=True, padx=(0, 4))
        ctk.CTkButton(btn_frame, text="Cancel", height=40,
                      fg_color="#ff3b3b",
                      command=self.destroy).pack(side="left", fill="x", expand=True)

    def _load_public_file(self):
        file = filedialog.askopenfile(filetypes=[("Key files", "*.pub"), ("Text files", "*.txt"), ("All", "*")])
        if file:
            self._public.delete("1.0", "end")
            self._public.insert("1.0", file.read())

    def _load_private_file(self):
        file = filedialog.askopenfile(filetypes=[("Key files", "*.pem"), ("Key files", "*.key"), ("Text files", "*.txt"), ("All", "*")])
        if file:
            self._private.delete("1.0", "end")
            self._private.insert("1.0", file.read())

    def _load_entry(self):
        entry_id, name, public_key, nonce, ciphertext = self.entry
        self._name.insert(0, name)
        self._public.insert("1.0", public_key)
        try:
            private_key = crypto.decrypt_password(nonce, ciphertext, self.vault_key)
            self._private.insert("1.0", private_key)
        except Exception:
            self._private.insert("1.0", "[Decryption failed]")

    def _save(self):
        name = self._name.get().strip()
        public = self._public.get("1.0", "end").strip()
        private = self._private.get("1.0", "end").strip()

        if not name or not private:
            messagebox.showerror("Error", "Key name and private key are required")
            return

        try:
            nonce, ciphertext = crypto.encrypt_password(private, self.vault_key)

            if self.entry:
                db.update_ssh_key(self.entry[0], name, public, nonce, ciphertext)
            else:
                db.add_ssh_key(name, public, nonce, ciphertext)

            self.on_save()
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save: {str(e)}")