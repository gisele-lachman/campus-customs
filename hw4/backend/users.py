"""User accounts: the only code allowed to write to the database.

Writes go through a separate connection with a SQLite "authorizer" that only
permits adding new rows to the users table. Any attempt to update or delete a
row, or to touch another table, is refused by SQLite itself.

All queries use ? placeholders, so user input is never pasted into SQL.
"""

import re
import sqlite3

import db
from passwords import burn_time, hash_password, verify_password

MIN_PASSWORD_LENGTH = 8
MAX_FIELD_LENGTH = 100
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# Columns that are safe to send to the website. password_hash is never included.
PUBLIC_COLUMNS = "id, name, email, first_name, last_name, created_at"


class SignupError(ValueError):
    """A problem with sign-up details, with a message safe to show the shopper."""


def normalize_email(email: str) -> str:
    return email.strip().lower()


def _users_only_authorizer(action, arg1, arg2, db_name, trigger):
    if action in (sqlite3.SQLITE_READ, sqlite3.SQLITE_SELECT, sqlite3.SQLITE_FUNCTION,
                  sqlite3.SQLITE_TRANSACTION):
        return sqlite3.SQLITE_OK
    if action == sqlite3.SQLITE_INSERT and arg1 == "users":
        return sqlite3.SQLITE_OK
    return sqlite3.SQLITE_DENY


def _users_writer() -> sqlite3.Connection:
    """Read-write connection that can only INSERT into the users table."""
    conn = sqlite3.connect(db.DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.set_authorizer(_users_only_authorizer)
    return conn


def get_user(user_id: int) -> dict | None:
    with db.connect() as conn:
        row = conn.execute(f"SELECT {PUBLIC_COLUMNS} FROM users WHERE id = ?", (user_id,)).fetchone()
    return dict(row) if row else None


def authenticate(email: str, password: str) -> dict | None:
    """Return the user if the email and password match, otherwise None."""
    with db.connect() as conn:
        row = conn.execute(
            f"SELECT {PUBLIC_COLUMNS}, password_hash FROM users WHERE lower(email) = ?",
            (normalize_email(email),),
        ).fetchone()
    if row is None:
        burn_time(password)
        return None
    if not verify_password(password, row["password_hash"]):
        return None
    user = dict(row)
    del user["password_hash"]
    return user


def create_user(first_name: str, last_name: str, email: str, password: str,
                confirm_password: str) -> dict:
    """Validate sign-up details, then add one row to the users table."""
    first_name, last_name = first_name.strip(), last_name.strip()
    email = normalize_email(email)

    if not all([first_name, last_name, email, password, confirm_password]):
        raise SignupError("Please fill in every field.")
    if max(len(first_name), len(last_name), len(email)) > MAX_FIELD_LENGTH:
        raise SignupError(f"Names and email must be under {MAX_FIELD_LENGTH} characters.")
    if not EMAIL_RE.match(email):
        raise SignupError("That doesn’t look like an email address.")
    if len(password) < MIN_PASSWORD_LENGTH:
        raise SignupError(f"Your password must be at least {MIN_PASSWORD_LENGTH} characters.")
    if password != confirm_password:
        raise SignupError("The passwords don’t match.")

    with db.connect() as conn:
        taken = conn.execute("SELECT 1 FROM users WHERE lower(email) = ?", (email,)).fetchone()
    if taken:
        raise SignupError("An account with that email already exists. Try logging in.")

    conn = _users_writer()
    try:
        with conn:  # commits on success, rolls back on error
            cur = conn.execute(
                "INSERT INTO users (name, email, password_hash, first_name, last_name) "
                "VALUES (?, ?, ?, ?, ?)",
                (f"{first_name} {last_name}", email, hash_password(password), first_name, last_name),
            )
            new_id = cur.lastrowid
    except sqlite3.IntegrityError:  # someone registered the same email a moment ago
        raise SignupError("An account with that email already exists. Try logging in.") from None
    finally:
        conn.close()
    return get_user(new_id)
