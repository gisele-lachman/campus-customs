"""Append-only audit trail of agent runs, in output/audit_trail.json.

One entry per tool call (or one "none" entry if the run used no tool), each with
the time, run id, shopper ("user#5" or "guest"), page, tool, short args, short
result, and the run's stop reason.

Safety of the file:
- Append only: we read the existing list, add entries, and write it back. Old
  entries are never removed. If the file isn't valid JSON we refuse to write
  rather than overwrite it.
- Atomic: the new version goes to a temporary file which then replaces the old
  one in a single step (os.replace), so a crash leaves either the old or the new
  file, both valid JSON.
- One writer at a time: a thread lock plus an OS file lock (fcntl), so two
  requests, or two server processes, can't interleave.
- Private data stays out: no message text, emails, passwords, hashes, or keys.
  Arguments and results are cleaned and capped.
- Never breaks the chat: any problem is logged as an error type and ignored.
"""

import fcntl
import json
import logging
import os
import re
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path

import sensitive
from limits import AUDIT_ARGS_CHARS, AUDIT_RESULT_CHARS

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output"
AUDIT_PATH = OUTPUT_DIR / "audit_trail.json"
LOCK_PATH = OUTPUT_DIR / ".audit_trail.lock"

STOP_REASONS = {
    "answered": "answered normally",
    "loop_limit": "hit the tool-call limit",
    "blocked_sensitive": "blocked by the sensitive-info guard",
    "provider_filter": "rejected by the AI provider's content filter",
    "error": "error",
}

log = logging.getLogger("uvicorn.error")
_thread_lock = threading.Lock()
_EMAIL = re.compile(r"[\w.+-]+@[\w-]+(\.[\w-]+)+")
_SECRET_WORDS = re.compile(r"(api[_ -]?key|pbkdf2|sk-[A-Za-z0-9]{8,})", re.IGNORECASE)


def clean(text: object, cap: int) -> str:
    """Make a value safe and short for the public log."""
    s = " ".join(str(text).split())
    if sensitive.check(s) or _SECRET_WORDS.search(s):
        return "[redacted]"
    s = _EMAIL.sub("[email]", s)
    return s if len(s) <= cap else s[: cap - 1] + "…"


def new_run_id() -> str:
    return uuid.uuid4().hex[:8]


def record_run(*, run_id: str, shopper: str, page: str | None, tool_calls: list[dict],
               stop_reason: str, note: str = "") -> None:
    """Write the entries for one agent run. Never raises."""
    try:
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        base = {
            "time": now,
            "run_id": run_id,
            "shopper": shopper,
            "page": clean(page or "-", 80),
            "stop_reason": stop_reason,
        }
        calls = tool_calls or [{"tool": "none", "args": "", "result": note or "replied without a tool"}]
        entries = [
            {
                **base,
                "step": f"{i}/{len(calls)}",
                "tool": c["tool"],
                "args": clean(c.get("args", ""), AUDIT_ARGS_CHARS),
                "result": clean(c.get("result", ""), AUDIT_RESULT_CHARS),
            }
            for i, c in enumerate(calls, 1)
        ]
        if tool_calls and note:
            entries[-1]["result"] = clean(f'{entries[-1]["result"]} | {note}', AUDIT_RESULT_CHARS)
        _append(entries)
    except Exception as e:  # the chat must keep working even if logging fails
        log.error("Audit trail not written: %s", type(e).__name__)


def _append(entries: list[dict]) -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)
    with _thread_lock, open(LOCK_PATH, "a") as lock_file:
        fcntl.flock(lock_file, fcntl.LOCK_EX)
        try:
            data: list = []
            if AUDIT_PATH.exists() and AUDIT_PATH.stat().st_size > 0:
                with open(AUDIT_PATH, encoding="utf-8") as f:
                    data = json.load(f)  # invalid JSON raises: we never overwrite a file we can't read
                if not isinstance(data, list):
                    raise ValueError("audit trail is not a JSON list")
            data.extend(entries)
            tmp = AUDIT_PATH.with_name(f".audit_trail.{os.getpid()}.{uuid.uuid4().hex[:6]}.tmp")
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=1, ensure_ascii=False)
                f.write("\n")
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp, AUDIT_PATH)  # atomic swap
        finally:
            fcntl.flock(lock_file, fcntl.LOCK_UN)
