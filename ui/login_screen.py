import customtkinter as ctk
import threading, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import database as db
import auth
import crypto


class LoginScreen(ctk.CTkFrame):
    def __init__(self, parent, on_success):
        super().__init__(parent, fg_color="transparent")
        self.parent = parent
        self.on_success = on_success

        db.initialize_db()
        self.is_first_run = db.is_first_run()
        self._build_ui()

    def _build_ui(self):
        container = ctk.CTkFrame(self, width=420, height=550)
        container.place(relx=0.5, rely=0.5, anchor="center")
        container.pack_propagate(False)

        ctk.CTkLabel(container, text="\U0001f510",
                     font=ctk.CTkFont(size=56)).pack(pady=(40, 6))
        ctk.CTkLabel(container, text="SecureVault",
                     font=ctk.CTkFont(size=28, weight="bold")).pack()

        subtitle = ("Create your master password to get started"
                    if self.is_first_run else
                    "Enter your master password to unlock your vault")
        ctk.CTkLabel(container, text=subtitle, font=ctk.CTkFont(size=13),
                     text_color="gray").pack(pady=(4, 22))

        self.pw_entry = ctk.CTkEntry(
            container, placeholder_text="Master Password",
            show="\u2022", width=320, height=46, font=ctk.CTkFont(size=14))
        self.pw_entry.pack(pady=4)

        self.confirm_entry = None
        if self.is_first_run:
            self.confirm_entry = ctk.CTkEntry(
                container, placeholder_text="Confirm Master Password",
                show="\u2022", width=320, height=46, font=ctk.CTkFont(size=14))
            self.confirm_entry.pack(pady=4)
            self.confirm_entry.bind("<Return>", lambda _: self._submit())

        self.error_lbl = ctk.CTkLabel(container, text="",
                                      text_color="#e05252",
                                      font=ctk.CTkFont(size=12))
        self.error_lbl.pack(pady=4)

        btn_text = "Create Vault" if self.is_first_run else "Unlock Vault"
        self.submit_btn = ctk.CTkButton(
            container, text=btn_text, width=320, height=46,
            font=ctk.CTkFont(size=15, weight="bold"),
            command=self._submit)
        self.submit_btn.pack(pady=6)

        if not self.is_first_run:
            ctk.CTkLabel(container,
                         text="Forgot your master password? It cannot be recovered.",
                         font=ctk.CTkFont(size=11),
                         text_color="gray").pack(pady=(10, 0))

        self.pw_entry.bind("<Return>", lambda _: self._submit())
        self.pw_entry.focus()

    def _set_loading(self, loading: bool):
        if loading:
            self.submit_btn.configure(state="disabled", text="Unlocking...")
            self.pw_entry.configure(state="disabled")
            if self.confirm_entry:
                self.confirm_entry.configure(state="disabled")
        else:
            btn_text = "Create Vault" if self.is_first_run else "Unlock Vault"
            self.submit_btn.configure(state="normal", text=btn_text)
            self.pw_entry.configure(state="normal")
            if self.confirm_entry:
                self.confirm_entry.configure(state="normal")

    def _submit(self):
        password = self.pw_entry.get()

        if not password:
            self.error_lbl.configure(text="Please enter your master password.")
            return
        if len(password) < 8:
            self.error_lbl.configure(
                text="Password must be at least 8 characters.")
            return

        if self.is_first_run:
            confirm = self.confirm_entry.get() if self.confirm_entry else ""
            if password != confirm:
                self.error_lbl.configure(
                    text="Passwords do not match. Try again.")
                return

        self.error_lbl.configure(text="")
        self._set_loading(True)

        # Run bcrypt in background so the UI does not freeze
        thread = threading.Thread(
            target=self._do_auth, args=(password,), daemon=True)
        thread.start()

    def _do_auth(self, password):
        try:
            if self.is_first_run:
                pw_hash   = auth.hash_password(password)
                vault_salt = crypto.generate_salt()
                db.save_master(pw_hash, vault_salt)
                vault_key = crypto.derive_key(password, vault_salt)
                self.after(0, lambda: self.on_success(vault_key))
            else:
                master = db.get_master()
                if not master:
                    self.after(0, lambda: self._auth_failed("No vault found. Please restart."))
                    return
                pw_hash, vault_salt = master
                if auth.verify_password(password, pw_hash):
                    vault_key = crypto.derive_key(password, vault_salt)
                    self.after(0, lambda: self.on_success(vault_key))
                else:
                    self.after(0, lambda: self._auth_failed(
                        "\u274c Incorrect password. Try again."))
        except Exception as e:
            self.after(0, lambda: self._auth_failed(f"Error: {e}"))

    def _auth_failed(self, message: str):
        self._set_loading(False)
        self.error_lbl.configure(text=message)
        self.pw_entry.delete(0, "end")
        self.pw_entry.focus()