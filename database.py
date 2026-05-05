import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vault.db")


def get_connection():
    return sqlite3.connect(DB_PATH)


def initialize_db():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS master (
                id            INTEGER PRIMARY KEY,
                password_hash BLOB NOT NULL,
                vault_salt    BLOB NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS entries (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                site       TEXT NOT NULL,
                username   TEXT NOT NULL,
                nonce      BLOB NOT NULL,
                ciphertext BLOB NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS ssh_keys (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                name       TEXT NOT NULL UNIQUE,
                public_key TEXT NOT NULL,
                nonce      BLOB NOT NULL,
                ciphertext BLOB NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()


def is_first_run() -> bool:
    with get_connection() as conn:
        result = conn.execute("SELECT COUNT(*) FROM master").fetchone()
        return result[0] == 0


def save_master(password_hash: bytes, vault_salt: bytes):
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO master (password_hash, vault_salt) VALUES (?, ?)",
            (password_hash, vault_salt),
        )
        conn.commit()


def get_master():
    with get_connection() as conn:
        return conn.execute(
            "SELECT password_hash, vault_salt FROM master WHERE id = 1"
        ).fetchone()


def add_entry(site: str, username: str, nonce: bytes, ciphertext: bytes):
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO entries (site, username, nonce, ciphertext) VALUES (?, ?, ?, ?)",
            (site, username, nonce, ciphertext),
        )
        conn.commit()


def get_all_entries():
    with get_connection() as conn:
        return conn.execute(
            "SELECT id, site, username, nonce, ciphertext FROM entries ORDER BY site"
        ).fetchall()


def delete_entry(entry_id: int):
    with get_connection() as conn:
        conn.execute("DELETE FROM entries WHERE id = ?", (entry_id,))
        conn.commit()


def update_entry(entry_id: int, site: str, username: str, nonce: bytes, ciphertext: bytes):
    with get_connection() as conn:
        conn.execute(
            "UPDATE entries SET site=?, username=?, nonce=?, ciphertext=? WHERE id=?",
            (site, username, nonce, ciphertext, entry_id),
        )
        conn.commit()


def add_ssh_key(name: str, public_key: str, nonce: bytes, ciphertext: bytes):
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO ssh_keys (name, public_key, nonce, ciphertext) VALUES (?, ?, ?, ?)",
            (name, public_key, nonce, ciphertext),
        )
        conn.commit()


def get_all_ssh_keys():
    with get_connection() as conn:
        return conn.execute(
            "SELECT id, name, public_key, nonce, ciphertext FROM ssh_keys ORDER BY name"
        ).fetchall()


def delete_ssh_key(key_id: int):
    with get_connection() as conn:
        conn.execute("DELETE FROM ssh_keys WHERE id = ?", (key_id,))
        conn.commit()


def update_ssh_key(key_id: int, name: str, public_key: str, nonce: bytes, ciphertext: bytes):
    with get_connection() as conn:
        conn.execute(
            "UPDATE ssh_keys SET name=?, public_key=?, nonce=?, ciphertext=? WHERE id=?",
            (name, public_key, nonce, ciphertext, key_id),
        )
        conn.commit()

def add_ssh_key(name: str, public_key: str, nonce: bytes, ciphertext: bytes):
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO ssh_keys (name, public_key, nonce, ciphertext) VALUES (?, ?, ?, ?)",
            (name, public_key, nonce, ciphertext),
        )
        conn.commit()

def get_all_ssh_keys():
    with get_connection() as conn:
        return conn.execute(
            "SELECT id, name, public_key, nonce, ciphertext FROM ssh_keys ORDER BY name"
        ).fetchall()
    
def delete_ssh_key(key_id: int):
    with get_connection() as conn:
        conn.execute("DELETE FROM ssh_keys WHERE id = ?", (key_id,))
        conn.commit()

def update_ssh_key(key_id: int, name: str, public_key: str, nonce: bytes, ciphertext: bytes):
    with get_connection() as conn:
        conn.execute(
            "UPDATE ssh_keys SET name=?, public_key=?, nonce=?, ciphertext=? WHERE id=?",
            (name, public_key, nonce, ciphertext, key_id),
        )
        conn.commit()