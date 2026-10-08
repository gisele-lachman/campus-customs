"""Saved chat history for logged-in shoppers, in the existing chat_messages table.

Columns used as they are: id, user_id, role, content, products_json, created_at.
New rows store only product ids in products_json, never prices or stock, e.g.
    {"product_ids": ["basic-hoodie-big-yale", ...], "search": {"query": "hoodies", "total_matches": 27}}
Older rows hold a list of full product copies; we only read their product_id.

Writes go through a separate connection whose SQLite authorizer only allows
adding rows to chat_messages and deleting from it. Every query is scoped by the
user_id that the server got from the login cookie.
"""

import json
import sqlite3

import db


def _chat_only_authorizer(action, arg1, arg2, db_name, trigger):
    if action in (sqlite3.SQLITE_READ, sqlite3.SQLITE_SELECT, sqlite3.SQLITE_FUNCTION,
                  sqlite3.SQLITE_TRANSACTION):
        return sqlite3.SQLITE_OK
    if action in (sqlite3.SQLITE_INSERT, sqlite3.SQLITE_DELETE) and arg1 == "chat_messages":
        return sqlite3.SQLITE_OK
    return sqlite3.SQLITE_DENY


def _chat_writer() -> sqlite3.Connection:
    """Read-write connection that can only INSERT into / DELETE from chat_messages."""
    conn = sqlite3.connect(db.DB_PATH)
    conn.set_authorizer(_chat_only_authorizer)
    return conn


def parse_products_json(raw: str | None) -> tuple[list[str], dict | None]:
    """Return (product ids, search info) from either the new or the old format."""
    if not raw:
        return [], None
    try:
        data = json.loads(raw)
    except ValueError:
        return [], None
    if isinstance(data, dict):  # new format
        ids = [i for i in data.get("product_ids", []) if isinstance(i, str)]
        return ids, data.get("search") if isinstance(data.get("search"), dict) else None
    if isinstance(data, list):  # old format: full product copies, keep only the ids
        return [p["product_id"] for p in data if isinstance(p, dict) and "product_id" in p], None
    return [], None


def save_exchange(user_id: int, user_text: str, reply_text: str,
                  product_ids: list[str], search: dict | None) -> None:
    """Save one shopper message and the assistant's reply, in one transaction."""
    products_json = json.dumps({"product_ids": product_ids, "search": search}) if product_ids or search else None
    conn = _chat_writer()
    try:
        with conn:
            conn.execute(
                "INSERT INTO chat_messages (user_id, role, content) VALUES (?, 'user', ?)",
                (user_id, user_text),
            )
            conn.execute(
                "INSERT INTO chat_messages (user_id, role, content, products_json) VALUES (?, 'assistant', ?, ?)",
                (user_id, reply_text, products_json),
            )
    finally:
        conn.close()


def recent_messages(user_id: int, limit: int) -> list[dict]:
    """The shopper's latest `limit` messages, oldest first."""
    with db.connect() as conn:
        rows = conn.execute(
            "SELECT id, role, content, products_json, created_at FROM chat_messages "
            "WHERE user_id = ? ORDER BY id DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
    messages = []
    for r in reversed(rows):
        ids, search = parse_products_json(r["products_json"])
        messages.append({
            "role": r["role"], "content": r["content"], "product_ids": ids,
            "search": search, "created_at": r["created_at"],
        })
    return messages


def clear_history(user_id: int) -> int:
    """Delete only this shopper's messages. Returns how many were removed."""
    conn = _chat_writer()
    try:
        with conn:
            return conn.execute("DELETE FROM chat_messages WHERE user_id = ?", (user_id,)).rowcount
    finally:
        conn.close()
