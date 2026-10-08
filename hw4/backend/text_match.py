"""Shared word cleaning for matching shopper wording against messy catalogue text.

Used by the chatbot tools (tools.py) and the Products page filter groups
(categories.py), so both treat "hoodies", "hooded sweatshirt", and "Hood" alike.
"""

import re

# Different ways people write the same thing -> one word.
SYNONYMS = [
    (r"\bt[\s-]?shirts?\b|\btees?\b", " tshirt "),
    (r"\bquarter[\s-]?zips?\b|\b1/4[\s-]?zips?\b|\b1 4 zip\b", " quarterzip "),
    (r"\bfull[\s-]?zips?\b", " fullzip "),
    (r"\bcrew[\s-]?necks?\b", " crewneck "),
    (r"\bhoodies\b|\bhoody\b|\bhoods?\b|\bhooded( sweatshirts?)?\b", " hoodie "),
    (r"\bgrey\b", " gray "),
    (r"\bsweaters?\b", " sweater "),
    (r"\blong[\s-]?sleeves?\b|\bl/s\b|\bl s\b", " longsleeve "),
    (r"\bshort[\s-]?sleeves?\b", " shortsleeve "),
    (r"\btri[\s-]?blend\b", " triblend "),
    (r"\bdouble[\s-]?knit\b", " doubleknit "),
    (r"\bunder armou?r\b", " ua "),
    (r"&", " and "),
]
def words(text: str) -> list[str]:
    text = text.lower().replace("’", "").replace("'", "")
    for pattern, replacement in SYNONYMS:
        text = re.sub(pattern, replacement, text)
    words = re.sub(r"[^a-z0-9]+", " ", text).split()
    # Treat simple plurals as singular ("crewnecks" -> "crewneck").
    return [w[:-1] if len(w) > 3 and w.endswith("s") and not w.endswith("ss") else w for w in words]
