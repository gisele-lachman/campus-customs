"""Tools the shop agent can call.

Every tool here only reads the database, through db.py's read-only connection,
so the agent can never change anything. Names shown to shoppers come from
display.display_name, the one place where names are tidied.
"""

import difflib
import logging
import re
from dataclasses import dataclass, field

from pydantic_ai import FunctionToolset, RunContext

import db
from display import display_name
from limits import (
    MAX_COMPARE, MAX_DESCRIPTION_CHARS, MAX_MATCHES, MAX_RELATED, MAX_SEARCH_RESULTS, MAX_SUGGESTIONS,
    MAX_TOOL_INPUT_CHARS,
)
from text_match import words as _words
from models import (
    ComparedProduct, ComparisonEntry, ProductComparison, ProductDetails, ProductLookup, ProductMatch,
    ProductSearch, SearchHit, SizeCheck, SizeStock,
)

log = logging.getLogger("uvicorn.error")  # shows up in the server output



@dataclass
class ShopDeps:
    """Per-request info passed to the agent and its tools. Built on the server only:
    the shopper comes from the login cookie, and the page product is re-checked in the database."""

    user_id: int | None = None  # None = guest
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    page: str | None = None
    current_product: ProductDetails | None = None  # verified product on the page being viewed
    # Filled in by search_products. After the run, agent.py turns these product ids
    # into cards using database rows, so cards never depend on what the model wrote.
    search: ProductSearch | None = field(default=None)
    # Every tool call in this run, for the audit trail (short, cleaned later in audit.py).
    tool_calls: list[dict] = field(default_factory=list)

    @property
    def is_guest(self) -> bool:
        return self.user_id is None


shop_tools: FunctionToolset[ShopDeps] = FunctionToolset()


def _record(ctx: RunContext[ShopDeps], tool: str, args: str, result: str) -> None:
    """Note a tool call for the server log and the audit trail."""
    log.info("TOOL %s(%s) -> %s", tool, args, result)
    ctx.deps.tool_calls.append({"tool": tool, "args": args, "result": result})


# ---------- Turning shopper wording into comparable words ----------

_FILLER = {"the", "a", "an", "please"}


def _product_words(p: dict) -> set[str]:
    return set(_words(p["display_name"])) | set(_words(p["name"])) | set(_words(p["product_id"]))


def _word_found(query_word: str, words: set[str]) -> bool:
    # Allow a short start of a word too ("hood" finds "hoodie"), but not tiny fragments.
    return query_word in words or (len(query_word) >= 4 and any(w.startswith(query_word) for w in words))


# ---------- Sizes ----------

_SIZE_ALIASES = {
    "XS": {"xs", "extra small", "x small", "xsmall"},
    "S": {"s", "small", "sm"},
    "M": {"m", "medium", "med", "md"},
    "L": {"l", "large", "lg"},
    "XL": {"xl", "extra large", "x large", "xlarge"},
    "XXL": {"xxl", "2xl", "xx large", "xxlarge", "2x", "extra extra large", "double xl"},
}


def normalize_size(text: str) -> str | None:
    key = re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()
    key = re.sub(r"^(size|a|an)\s+", "", key)
    for size, aliases in _SIZE_ALIASES.items():
        if key in aliases:
            return size
    return None


# ---------- Finding products ----------

def _catalogue() -> list[dict]:
    products = db.list_products()
    for p in products:
        p["display_name"] = display_name(p["name"])
    return products


def _as_match(p: dict) -> ProductMatch:
    return ProductMatch(product_id=p["product_id"], name=p["display_name"])


def find_products(query: str) -> tuple[list[dict], list[dict]]:
    """Return (matches, suggestions) for a product id, name, or part of a name."""
    products = _catalogue()
    q = query.strip().lower()

    by_id = [p for p in products if p["product_id"] == q]
    if by_id:
        return by_id, []

    q_words = [w for w in _words(query) if w not in _FILLER]
    if not q_words:
        return [], []
    exact = [p for p in products if _words(p["display_name"]) == q_words or _words(p["name"]) == q_words]
    if exact:
        return exact, []

    matches = [p for p in products if all(_word_found(w, _product_words(p)) for w in q_words)]
    if matches:
        return matches, []

    # Nothing contains every word: offer close names, but never treat them as a match.
    q_text = " ".join(q_words)
    scored = sorted(
        ((difflib.SequenceMatcher(None, q_text, " ".join(_words(p["display_name"]))).ratio(), p) for p in products),
        key=lambda pair: pair[0],
        reverse=True,
    )
    return [], [p for score, p in scored[:MAX_SUGGESTIONS] if score >= 0.6]


def product_details(product_id: str) -> ProductDetails | None:
    """Verified details for a product id, or None if the id isn't in the database."""
    return _details(product_id) if db.get_product(product_id) else None


def _details(product_id: str) -> ProductDetails:
    p = db.get_product(product_id)
    stock = [SizeStock(size=s["size"], quantity=s["quantity"]) for s in p["inventory"]]
    return ProductDetails(
        product_id=p["product_id"],
        name=display_name(p["name"]),
        garment_type=p["garment_type"],
        description=p["description"][:MAX_DESCRIPTION_CHARS],
        price=p["price"],
        colors=p["colors"],
        stock_by_size=stock,
        in_stock_sizes=[s.size for s in stock if s.quantity > 0],
        sold_out_sizes=[s.size for s in stock if s.quantity == 0],
        total_stock=p["total_stock"],
    )


def _size_check(details: ProductDetails, requested: str) -> SizeCheck:
    size = normalize_size(requested)
    quantity = next((s.quantity for s in details.stock_by_size if s.size == size), None)
    return SizeCheck(requested=requested, size=size, exists=quantity is not None, quantity=quantity)


# ---------- Tools ----------

@shop_tools.tool
def lookup_product(ctx: RunContext[ShopDeps], product: str, size: str | None = None) -> ProductLookup:
    """Look up one product's price, description, colors, and stock from the shop database.

    Call this for ANY question about a specific product's price, description, colors, or stock.

    Args:
        product: The product id if known, or the product name or part of it in the shopper's words
            (e.g. "basic hoodie big yale", "Morse quarter zip", "boola boola tee").
        size: Optional size the shopper asked about, as they wrote it (e.g. "M", "medium", "XXL").

    Returns status "found" with full details (and size_check if a size was given),
    "multiple_matches" with candidate names to ask the shopper about, or
    "not_found" with possibly a few close suggestions.
    """
    product = product[:MAX_TOOL_INPUT_CHARS]
    matches, suggestions = find_products(product)

    if len(matches) == 1:
        details = _details(matches[0]["product_id"])
        result = ProductLookup(
            status="found",
            product=details,
            size_check=_size_check(details, size[:40]) if size else None,
            total_matches=1,
        )
    elif matches:
        result = ProductLookup(
            status="multiple_matches",
            matches=[_as_match(p) for p in matches[:MAX_MATCHES]],
            total_matches=len(matches),
        )
    else:
        result = ProductLookup(status="not_found", matches=[_as_match(p) for p in suggestions])

    summary = result.status + (
        f" [{result.product.product_id}]" if result.product else f" ({result.total_matches} matches)"
    )
    _record(ctx, "lookup_product", f"product={product!r}, size={size!r}", summary)
    return result


# ---------- Searching the catalogue by type, theme, or color ----------

# Words that say nothing about which product is wanted (every item is Yale merch).
_SEARCH_NOISE = _FILLER | {
    "do", "you", "have", "any", "anything", "something", "with", "on", "it", "in", "what",
    "which", "show", "me", "some", "item", "stuff", "gear", "merch", "apparel", "clothing",
    "clothe", "yale", "your", "got", "sell", "for", "of", "is", "there", "and", "or", "color",
}

# Words for a kind of garment. These only count in a product's name or garment type,
# so "crewneck" doesn't match a T-shirt whose description mentions a crew neckline.
_GARMENT_WORDS = {
    "hoodie", "tshirt", "crewneck", "quarterzip", "fullzip", "jacket", "fleece", "longsleeve",
    "shortsleeve", "mockneck", "sweatshirt", "sweater", "pullover", "bomber", "crew",
}

# How strongly a word counts depending on where it appears in a product.
_FIELD_WEIGHTS = {"name": 3, "type": 3, "tags": 2, "colors": 2, "description": 1}


def _search_index() -> tuple[list[dict], set[str]]:
    """Catalogue rows with their words split by field, plus every word used in a color."""
    products = _catalogue()
    color_words: set[str] = set()
    for p in products:
        p["fields"] = {
            "name": _product_words(p),
            "type": set(_words(p["garment_type"])),
            "tags": {w for tag in p["search_tags"] for w in _words(tag)},
            "colors": {w for c in p["colors"] for w in _words(c)},
            "description": set(_words(p["description"])),
        }
        color_words |= p["fields"]["colors"]
    return products, color_words


def _score(p: dict, word: str, color_words: set[str]) -> int:
    """Best weight for one query word in one product (0 = not found).

    Color words only count in the colors list, so "navy" doesn't match a gray
    shirt that merely has navy lettering in its description. Garment words only
    count in the name or garment type.
    """
    if word in color_words:
        fields = ["colors"]
    elif word in _GARMENT_WORDS:
        fields = ["name", "type"]
    else:
        fields = list(_FIELD_WEIGHTS)
    return max((_FIELD_WEIGHTS[f] for f in fields if word in p["fields"][f]), default=0)


def _hit(p: dict) -> SearchHit:
    return SearchHit(
        product_id=p["product_id"],
        name=p["display_name"],
        garment_type=p["garment_type"],
        price=p["price"],
        in_stock=p["total_stock"] > 0,
    )


def search_catalogue(query: str) -> ProductSearch:
    """Every product containing all the query words, best matches first."""
    products, color_words = _search_index()
    words = [w for w in dict.fromkeys(_words(query)) if w not in _SEARCH_NOISE]

    scored = []
    for p in products:
        scores = [_score(p, w, color_words) for w in words]
        if words and all(scores):
            scored.append((sum(scores), p))
    # Best score first; in-stock items before sold-out ones; then by name.
    scored.sort(key=lambda pair: (-pair[0], pair[1]["total_stock"] == 0, pair[1]["display_name"]))
    results = [_hit(p) for _, p in scored[:MAX_SEARCH_RESULTS]]

    related = []
    if not scored and len(words) > 1:
        # Nothing has every word: offer real items that match part of the request.
        partial = [(sum(_score(p, w, color_words) for w in words), p) for p in products]
        partial = sorted((pair for pair in partial if pair[0] > 0), key=lambda pair: -pair[0])
        related = [_hit(p) for _, p in partial[:MAX_RELATED]]

    return ProductSearch(
        query=query, total_matches=len(scored), shown=len(results), results=results, related=related
    )


@shop_tools.tool
def search_products(ctx: RunContext[ShopDeps], query: str) -> ProductSearch:
    """Search the catalogue for a TYPE or CATEGORY of item; matches are shown as cards on the page.

    Use this when the shopper asks what the shop has, e.g. "what hoodies do you have?",
    "anything with a bulldog?", "Davenport gear", "navy quarter-zips", "soccer shirts".
    Do NOT use it for one specific product's price, description, or stock (use lookup_product).

    Args:
        query: A few keywords for what they want: item type, theme (college, school, sport,
            bulldog), and/or color, e.g. "hoodie", "bulldog", "navy crewneck", "Davenport".

    Returns total_matches (the true count), shown (how many cards appear, at most 12),
    results (best first, these become the cards), and, only if nothing matched,
    a few related real items that match part of the request.
    """
    result = search_catalogue(query[:MAX_TOOL_INPUT_CHARS])
    if any(w not in _SEARCH_NOISE for w in _words(query)):
        ctx.deps.search = result  # the backend builds the cards from these ids
    summary = f"{result.total_matches} matches, showing {result.shown}" + (
        f", {len(result.related)} related" if result.related else ""
    )
    _record(ctx, "search_products", f"query={query!r}", summary)
    return result


# ---------- Comparing two or three products ----------



def _compare_entry(requested: str) -> ComparisonEntry:
    """Resolve one named product the same way lookup_product does."""
    matches, suggestions = find_products(requested)
    if len(matches) == 1:
        d = _details(matches[0]["product_id"])
        product = ComparedProduct(
            product_id=d.product_id, name=d.name, price=d.price, colors=d.colors,
            stock_by_size=d.stock_by_size, in_stock_sizes=d.in_stock_sizes,
            sold_out_sizes=d.sold_out_sizes, total_stock=d.total_stock,
        )
        return ComparisonEntry(requested=requested, status="found", product=product, total_matches=1)
    if matches:
        return ComparisonEntry(
            requested=requested, status="multiple_matches",
            matches=[_as_match(p) for p in matches[:MAX_MATCHES]], total_matches=len(matches),
        )
    return ComparisonEntry(requested=requested, status="not_found", matches=[_as_match(p) for p in suggestions])


def compare_catalogue(products: list[str]) -> ProductComparison:
    entries = [_compare_entry(name[:MAX_TOOL_INPUT_CHARS]) for name in products[:MAX_COMPARE]]
    found = [e.product for e in entries if e.product]

    if len(products) < 2:
        note = "Name at least two products to compare."
    elif len(products) > MAX_COMPARE:
        note = f"Only the first {MAX_COMPARE} products were compared."
    else:
        note = None
    if len(found) < len(entries):
        note = "Some products couldn't be pinned down; ask the shopper about those first."
    elif len({p.product_id for p in found}) < len(found):
        note = "Two of the names point to the same product."

    ready = note is None and len(found) >= 2
    if not ready:
        return ProductComparison(entries=entries, ready=False, note=note)

    low = min(p.price for p in found)
    common = [s for s in found[0].in_stock_sizes if all(s in p.in_stock_sizes for p in found)]
    return ProductComparison(
        entries=entries,
        ready=True,
        cheapest=[p.name for p in found if p.price == low],
        price_difference=round(max(p.price for p in found) - low, 2),
        sizes_in_stock_in_all=common,
    )


@shop_tools.tool
def compare_products(ctx: RunContext[ShopDeps], products: list[str]) -> ProductComparison:
    """Compare two or three specific products side by side: price, colors, and stock by size.

    Use this when the shopper wants to compare or choose between named products, e.g.
    "which is cheaper, the Morse quarter-zip or the Berkeley quarter-zip?" or
    "compare the Yale Dad Hoodie and the Yale Mom Hoodie". "This" can be the product
    being viewed (pass its product_id).

    Args:
        products: Two or three product ids or names, in the shopper's words.

    Each entry has status found / multiple_matches / not_found, like lookup_product.
    Only when `ready` is true are cheapest, price_difference, and sizes_in_stock_in_all filled.
    """
    result = compare_catalogue(products)
    summary = (
        f"ready; cheapest: {', '.join(e.product.product_id for e in result.entries if e.product and e.product.name in result.cheapest)}"
        if result.ready else ", ".join(e.status for e in result.entries)
    )
    _record(ctx, "compare_products", f"products={[p[:40] for p in products]}", summary)
    return result
