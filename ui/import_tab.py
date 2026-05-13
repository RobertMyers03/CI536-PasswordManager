import customtkinter as ctk
from tkinter import filedialog, messagebox
import csv
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import database as db
import crypto

KNOWN_FORMATS = {
    "bitwarden": {"name": "name",     "username": "username", "password": "password"},
    "chrome":    {"name": "name",     "username": "username", "password": "password"},
    "firefox":   {"name": "hostname", "username": "username", "password": "password"},
}

def _detect_format(headers):
    h = [x.strip().lower() for x in headers]
    if "hostname" in h:
        return "firefox"
    if "url" in h or "login_uri" in h:
        return "chrome"
    return "bitwarden"


class ImportTab(ctk.CTkFrame):
    def __init__(self, master, vault_key, on_import_done, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.vault_key      = vault_key
        self.on_import_done = on_import_done
        self._rows          = []   
        self._build_ui()
    def _build_ui(self):
        ctk.CTkLabel(self, text="Import Passwords",
                     font=ctk.CTkFont(size=22, weight="bold")).pack(pady=(20, 4))
        ctk.CTkLabel(self, text="Import a CSV exported from Bitwarden, Chrome or Firefox.",
                     text_color="gray").pack(pady=(0, 20))

        step1 = ctk.CTkFrame(self, corner_radius=10)
        step1.pack(fill="x", padx=40, pady=6)

        ctk.CTkLabel(step1, text="Step 1 — Choose CSV file",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     anchor="w").pack(fill="x", padx=16, pady=(14, 6))

        file_row = ctk.CTkFrame(step1, fg_color="transparent")
        file_row.pack(fill="x", padx=16, pady=(0, 14))
        file_row.columnconfigure(0, weight=1)

        self._path_var = ctk.StringVar(value="No file selected")
        ctk.CTkEntry(file_row, textvariable=self._path_var,
                     state="readonly", height=38).grid(row=0, column=0,
                                                        sticky="ew", padx=(0, 8))
        ctk.CTkButton(file_row, text="Browse…", width=100, height=38,
                      command=self._browse).grid(row=0, column=1)

        step2 = ctk.CTkFrame(self, corner_radius=10)
        step2.pack(fill="x", padx=40, pady=6)

        ctk.CTkLabel(step2, text="Step 2 — Preview",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     anchor="w").pack(fill="x", padx=16, pady=(14, 6))

        self._preview_label = ctk.CTkLabel(
            step2,
            text="Load a file to see a preview.",
            text_color="gray", anchor="w", justify="left")
        self._preview_label.pack(fill="x", padx=16, pady=(0, 14))

        self._import_btn = ctk.CTkButton(
            self, text="\u2b07  Import into Vault",
            height=46, font=ctk.CTkFont(size=14, weight="bold"),
            state="disabled", command=self._do_import)
        self._import_btn.pack(padx=40, pady=12, fill="x")

        self._log = ctk.CTkScrollableFrame(self, corner_radius=10, height=200)
        self._log.pack(fill="both", expand=True, padx=40, pady=(0, 20))

    def _browse(self):
        path = filedialog.askopenfilename(
            title="Select CSV export",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")])
        if not path:
            return

        self._path_var.set(path)
        self._rows = []
        self._clear_log()

        try:
            with open(path, newline="", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                headers = reader.fieldnames or []
                fmt = _detect_format(headers)
                mapping = KNOWN_FORMATS[fmt]

                for row in reader:
                    name  = row.get(mapping["name"],     "").strip()
                    user  = row.get(mapping["username"],  "").strip()
                    pw    = row.get(mapping["password"],  "").strip()
                    if name and pw:
                        self._rows.append({"site": name, "username": user, "password": pw})

        except Exception as e:
            messagebox.showerror("Error", f"Could not read file:\n{e}")
            return

        total = len(self._rows)
        if total == 0:
            self._preview_label.configure(
                text="No valid entries found in that file. Make sure it is a Bitwarden, Chrome or Firefox CSV.")
            self._import_btn.configure(state="disabled")
            return

        sample = self._rows[:3]
        lines = [f"  • {r['site']}  ({r['username'] or 'no username'})" for r in sample]
        if total > 3:
            lines.append(f"  … and {total - 3} more")

        self._preview_label.configure(
            text=f"Found {total} entr{'y' if total == 1 else 'ies'}:\n" + "\n".join(lines))
        self._import_btn.configure(state="normal")

    def _do_import(self):
        if not self._rows:
            return

        self._clear_log()

        existing = {
            (e[1].lower(), e[2].lower())
            for e in db.get_all_entries()
        }

        imported   = 0
        duplicates = 0
        errors     = 0

        for row in self._rows:
            key = (row["site"].lower(), row["username"].lower())

            if key in existing:
                duplicates += 1
                self._log_line(f"\u26a0  Duplicate — skipped:  {row['site']}  ({row['username']})",
                               color="#e09b52")
                continue

            try:
                nonce, ct = crypto.encrypt_password(row["password"], self.vault_key)
                db.add_entry(row["site"], row["username"], nonce, ct)
                existing.add(key)
                imported += 1
                self._log_line(f"\u2705  Imported:  {row['site']}  ({row['username']})",
                               color="#52c07a")
            except Exception as e:
                errors += 1
                self._log_line(f"\u274c  Error on {row['site']}: {e}", color="#e05252")

        summary = (f"Done — {imported} imported"
                   + (f", {duplicates} duplicate{'s' if duplicates != 1 else ''} skipped" if duplicates else "")
                   + (f", {errors} error{'s' if errors != 1 else ''}" if errors else ""))
        self._log_line("\u2500" * 55, color="gray")
        self._log_line(summary,
                       color="#52c07a" if errors == 0 else "#e09b52",
                       bold=True)

        self._rows = []
        self._import_btn.configure(state="disabled")
        self._path_var.set("No file selected")
        self._preview_label.configure(text="Load a file to see a preview.")

        if imported > 0:
            self.on_import_done()

    def _log_line(self, text, color="white", bold=False):
        ctk.CTkLabel(
            self._log, text=text, anchor="w",
            text_color=color,
            font=ctk.CTkFont(size=12, weight="bold" if bold else "normal")
        ).pack(fill="x", padx=8, pady=1)

    def _clear_log(self):
        for w in self._log.winfo_children():
            w.destroy()
