import customtkinter as ctk

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class SecureVaultApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("SecureVault \u2014 Password Manager")
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
    app = SecureVaultApp()
    app.mainloop()
