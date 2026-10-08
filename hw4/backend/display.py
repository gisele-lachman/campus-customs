"""Turn raw database rows into shopper-friendly display values.

This is the single place where product names are tidied up. The website and
(later) the chatbot should both use `display_name` / `to_display` so a product
is always called the same thing. The database itself is never changed.
"""

import re

from categories import color_groups, type_group

# Exact fixes for names that general rules can't sensibly repair.
NAME_OVERRIDES = {
    "Champion Reverse Weave Hoodie 1": "Champion Reverse Weave Hoodie",
    "Squash Left Chest Tennis": "Squash Left Chest Crewneck",
    "Yale Sports Creqneck Field Hockey": "Yale Sports Crewneck Field Hockey",
}

# (pattern, replacement) pairs applied in order to every name.
NAME_RULES = [
    (r"\b1 4 Zip\b", "1/4 Zip"),
    (r"\bL S\b", "L/S"),
    (r"\b(\d) (\d)$", r"\1.\2"),  # "2 0" -> "2.0"
    (r"\bT Shirt\b", "T-Shirt"),
    (r"\bTri Blend\b", "Tri-Blend"),
    (r"\bFull Zip\b", "Full-Zip"),
    (r"\bDouble Knit\b", "Double-Knit"),
    (r"\bTrack Field\b", "Track and Field"),
    (r"\bUa\b", "UA"),
    (r"\bVit\b", "VIT"),
    (r"\bMens\b", "Men's"),
    (r"\bWomens\b", "Women's"),
    (r"\bVs\b", "vs."),
    (r"(?<=\w )(Of|And|The)\b", lambda m: m.group(1).lower()),  # small words mid-name
]


def display_name(raw_name: str) -> str:
    """Return a tidy, human-friendly version of a catalogue name."""
    name = NAME_OVERRIDES.get(raw_name, raw_name)
    for pattern, replacement in NAME_RULES:
        name = re.sub(pattern, replacement, name)
    return name


def image_url(image_file_path: str) -> str:
    """Map a DB path like 'products/x.jpg' to the URL the backend serves it at."""
    return "/images/" + image_file_path.removeprefix("products/")


def short_description(text: str, limit: int = 110) -> str:
    """First sentence of the description, trimmed for product cards."""
    first = text.split(". ")[0].rstrip(".") + "."
    if len(first) <= limit:
        return first
    return first[:limit].rsplit(" ", 1)[0] + "…"


def to_display(product: dict) -> dict:
    """Add display fields to a product dict from db.py (keeps the raw name too)."""
    return {
        **product,
        "raw_name": product["name"],
        "name": display_name(product["name"]),
        "image_url": image_url(product["image_file_path"]),
        "short_description": short_description(product["description"]),
        "type_group": type_group(product["garment_type"], product["name"]),
        "color_groups": color_groups(product["colors"]),
    }
