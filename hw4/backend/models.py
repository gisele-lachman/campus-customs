"""Structured types for the chat route and the agent's replies."""

from typing import Literal

from pydantic import BaseModel, Field

from limits import MAX_MESSAGE_LENGTH


# ----- What the website sends to POST /api/chat -----

class ChatTurn(BaseModel):
    """One earlier message in a guest's conversation (logged-in history comes from the database)."""

    role: Literal["user", "assistant"]
    content: str = Field(max_length=MAX_MESSAGE_LENGTH)
    product_ids: list[str] = Field(default_factory=list, max_length=12, description="Cards shown with it")


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=MAX_MESSAGE_LENGTH)
    history: list[ChatTurn] = Field(default_factory=list, max_length=40)
    page: str | None = Field(default=None, max_length=300, description="Path the shopper is on")
    product_id: str | None = Field(default=None, max_length=200, description="Product on that page, if any")


# ----- What the agent returns (and the route sends back) -----

class ProductCard(BaseModel):
    """A product card for the website, built by the backend from a database row."""

    product_id: str
    name: str
    price: float
    image_url: str
    short_info: str


class AgentReply(BaseModel):
    """What the model itself writes: only the text. Cards are added by the backend."""

    reply: str = Field(description="The message to show the shopper.")


class SearchSummary(BaseModel):
    """Tells the website that the cards are search results, and how many matched."""

    query: str
    total_matches: int
    shown: int


class ChatReply(BaseModel):
    """What POST /api/chat returns to the website."""

    reply: str
    products: list[ProductCard] = Field(
        default_factory=list,
        description="Cards built by the backend from database rows (never from model text).",
    )
    search: SearchSummary | None = None
    stopped: bool = Field(default=False, description="True if the run stopped early (loop limit or provider content filter); not saved")
    blocked: bool = Field(
        default=False,
        description="True if the sensitive-info guard stopped the message (not sent to the model or saved)",
    )


class HistoryMessage(BaseModel):
    """A saved message sent back to the chat window, with cards rebuilt from live data."""

    role: Literal["user", "assistant"]
    content: str
    products: list[ProductCard] = Field(default_factory=list)
    search: SearchSummary | None = None


# ----- What the lookup_product tool returns to the agent (tools.py) -----

class SizeStock(BaseModel):
    size: str = Field(description="One of XS, S, M, L, XL, XXL")
    quantity: int = Field(description="Units in stock. 0 means sold out in this size.")


class ProductDetails(BaseModel):
    """Everything the agent may say about one product, straight from the database."""

    product_id: str
    name: str = Field(description="Tidied display name. Use this name with shoppers.")
    garment_type: str
    description: str
    price: float = Field(description="Price in US dollars")
    colors: list[str]
    stock_by_size: list[SizeStock]
    in_stock_sizes: list[str]
    sold_out_sizes: list[str]
    total_stock: int = Field(description="Units in stock across all sizes")


class SizeCheck(BaseModel):
    """Answer for the one size the shopper asked about."""

    requested: str = Field(description="The size exactly as the shopper wrote it")
    size: str | None = Field(description="Standard size it maps to, or null if it isn't a size we sell")
    exists: bool = Field(description="False if this item doesn't come in that size")
    quantity: int | None = Field(description="Units in stock in that size (0 = sold out)")


class ProductMatch(BaseModel):
    """A short candidate entry, used to ask the shopper which product they mean."""

    product_id: str
    name: str


class ProductLookup(BaseModel):
    status: Literal["found", "multiple_matches", "not_found"]
    product: ProductDetails | None = Field(default=None, description="Set when status is found")
    size_check: SizeCheck | None = Field(default=None, description="Set when found and a size was asked")
    matches: list[ProductMatch] = Field(
        default_factory=list,
        description="multiple_matches: the candidates. not_found: close suggestions (may be empty).",
    )
    total_matches: int = Field(default=0, description="How many products matched before capping the list")


# ----- What the search_products tool returns to the agent (tools.py) -----

class SearchHit(BaseModel):
    """One search result, kept small: the website card shows the rest."""

    product_id: str
    name: str = Field(description="Tidied display name")
    garment_type: str
    price: float
    in_stock: bool = Field(description="False if sold out in every size")


class ProductSearch(BaseModel):
    query: str
    total_matches: int = Field(description="How many products matched before capping")
    shown: int = Field(description="How many are shown as cards on the page (at most 12)")
    results: list[SearchHit] = Field(description="Best matches first; these become the cards")
    related: list[SearchHit] = Field(
        default_factory=list,
        description="Only when nothing matched: real items matching part of the request (may be empty)",
    )


# ----- What the compare_products tool returns to the agent (tools.py) -----

class ComparedProduct(BaseModel):
    """The facts needed to compare one product, straight from the database."""

    product_id: str
    name: str = Field(description="Tidied display name")
    price: float
    colors: list[str]
    stock_by_size: list[SizeStock]
    in_stock_sizes: list[str]
    sold_out_sizes: list[str]
    total_stock: int


class ComparisonEntry(BaseModel):
    """One product the shopper named, and whether it could be pinned down."""

    requested: str = Field(description="The product exactly as the shopper named it")
    status: Literal["found", "multiple_matches", "not_found"]
    product: ComparedProduct | None = None
    matches: list[ProductMatch] = Field(
        default_factory=list, description="Candidates (ambiguous) or suggestions (not found)"
    )
    total_matches: int = 0


class ProductComparison(BaseModel):
    entries: list[ComparisonEntry]
    ready: bool = Field(description="True only if every product was found and they are all different")
    cheapest: list[str] = Field(default_factory=list, description="Name(s) of the cheapest; several if tied")
    price_difference: float | None = Field(default=None, description="Most expensive minus cheapest, in dollars")
    sizes_in_stock_in_all: list[str] = Field(
        default_factory=list, description="Sizes in stock for every compared product"
    )
    note: str | None = Field(default=None, description="Why the comparison isn't ready, if it isn't")
