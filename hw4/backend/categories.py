"""Clean filter groups for the Products page, built from messy catalogue text.

Uses the same word cleaning as the chatbot search (text_match.words), so a
product the chatbot calls a hoodie is also under "Hoodies" in the filters.
"""

from text_match import words

# Checked in order; the first rule whose word appears wins. The garment type is
# checked before the name, so a "Crewneck" whose garment type says quarter-zip
# is filed as a quarter-zip, and "Crew Left Chest Hoodie" (rowing) is a hoodie.
TYPE_RULES = [
    ("Hoodies", {"hoodie"}),
    ("Quarter-Zips", {"quarterzip"}),
    ("T-Shirts", {"tshirt"}),
    ("Long Sleeves", {"longsleeve"}),
    ("Jackets & Fleece", {"jacket", "fleece", "bomber", "fullzip"}),
    ("Crewnecks", {"crewneck", "crew", "mockneck", "sweatshirt", "sweater"}),
]
OTHER_TYPE = "Other"

# Color words -> group. A color like "dark heather charcoal" lands in Gray.
COLOR_RULES = [
    ("Navy", {"navy"}),
    ("Gray", {"gray", "charcoal", "heather"}),
    ("White & Cream", {"white", "cream", "ivory"}),
    ("Blue", {"blue"}),  # after Navy, so "navy blue" is Navy, "royal blue" is Blue
    ("Red", {"red"}),
    ("Pink & Coral", {"pink", "coral"}),
    ("Green", {"green"}),
    ("Gold & Yellow", {"gold", "yellow"}),
    ("Black", {"black"}),
    ("Multicolor", {"multicolor"}),
]


def type_group(garment_type: str, name: str) -> str:
    for text in (garment_type, name):
        found = set(words(text))
        for group, keys in TYPE_RULES:
            if found & keys:
                return group
    return OTHER_TYPE


def color_group(color: str) -> str | None:
    found = set(words(color))
    for group, keys in COLOR_RULES:
        if found & keys:
            return group
    return None


def color_groups(colors: list[str]) -> list[str]:
    """Distinct color groups for a product's color list, in a stable order."""
    groups = {g for g in (color_group(c) for c in colors) if g}
    return [g for g, _ in COLOR_RULES if g in groups]
