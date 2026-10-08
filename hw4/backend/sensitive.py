"""Sensitive-info guard: spot passwords and full card numbers in chat messages.

Checked before a message reaches the AI model, the chat history, or the logs.
The rules are deliberately narrow so normal shopping messages ("under $70?",
"size XL", "the 2025 tee") are never blocked:

- card: 13-19 digits (spaces or dashes allowed between them) that also pass the
  Luhn checksum every real card number passes.
- password: the word password/passcode/pwd/pw followed by "is", ":" or "=" and
  a value, e.g. "my password is hunter22" ("I forgot my password" is fine).
"""

import re
from typing import Literal

SensitiveKind = Literal["card", "password"]

_CARD_CANDIDATE = re.compile(r"(?<![\d.$])\d(?:[ -]?\d){12,18}(?![\d.])")
_PASSWORD = re.compile(
    r"\b(?:pass(?:word|code|phrase)|pwd|pw)\b\s*(?:is|was|=|:)\s*[\"'“]?([^\s\"'”]{3,})",
    re.IGNORECASE,
)
# Words that can follow "password is" in a normal sentence ("my password is too short").
_NOT_A_PASSWORD = {
    "too", "not", "wrong", "incorrect", "invalid", "the", "a", "an", "my", "your", "required",
    "needed", "reset", "changed", "expired", "weak", "strong", "short", "long", "correct",
    "right", "different", "same", "case", "this", "that", "it", "what", "how", "fine", "ok",
    "okay", "working", "broken", "missing", "forgotten", "lost", "safe", "secret", "private",
}

WARNING = (
    "For your safety, I didn’t send that message to the assistant or save it. "
    "It looked like it might contain a password or a card number. Campus Customs’ "
    "shopping assistant never needs those, so please don’t share them in chat. "
    "If you meant something else, try rephrasing without the private details. "
    "What Yale gear can I help you find?"
)


def _luhn_ok(digits: str) -> bool:
    total = 0
    for i, ch in enumerate(reversed(digits)):
        n = int(ch)
        if i % 2 == 1:
            n *= 2
            if n > 9:
                n -= 9
        total += n
    return total % 10 == 0


def check(text: str) -> SensitiveKind | None:
    """Return what kind of sensitive info the text seems to contain, or None."""
    for match in _CARD_CANDIDATE.finditer(text):
        digits = re.sub(r"\D", "", match.group())
        if 13 <= len(digits) <= 19 and _luhn_ok(digits):
            return "card"
    for match in _PASSWORD.finditer(text):
        if match.group(1).lower().strip(".,!?") not in _NOT_A_PASSWORD:
            return "password"
    return None
