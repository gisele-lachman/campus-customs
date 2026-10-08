"""The Campus Customs shopping agent (PydanticAI + OpenAI via Portkey).

- System prompt: loaded once at startup from prompts/prompt.md
- Model: CHAT_MODEL below (override with CHAT_MODEL in .env)
- Tools: the shop_tools toolset from tools.py
- Output: the model writes only the reply text (AgentReply). If it searched,
  the backend then builds product cards from database rows (see _cards_for).
"""

import logging
import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from openai import AsyncOpenAI
from pydantic_ai import Agent, RunContext
from pydantic_ai.exceptions import ModelHTTPError, UsageLimitExceeded
from pydantic_ai.usage import UsageLimits
from pydantic_ai.messages import ModelMessage, ModelRequest, ModelResponse, TextPart, UserPromptPart
from pydantic_ai.models.openai import OpenAIResponsesModel, OpenAIResponsesModelSettings
from pydantic_ai.providers.openai import OpenAIProvider

import audit
import chat_history
import sensitive
import db
from display import to_display
from limits import (
    AGENT_HISTORY_LIMIT, HISTORY_LIMIT, MAX_MODEL_REQUESTS_PER_MESSAGE, MAX_TOOL_CALLS_PER_MESSAGE,
)
from models import AgentReply, ChatReply, ChatRequest, HistoryMessage, ProductCard, SearchSummary
from tools import ShopDeps, product_details, shop_tools

load_dotenv(Path(__file__).resolve().parent.parent / ".env")
log = logging.getLogger("uvicorn.error")  # shows up in the server output

# ---- Model choice: the one place to change it ----
# Checked against the Portkey model list (Oct 2026). Names not on that list silently
# fall back to gpt-5.6-luna, so always copy names exactly from the list.
# gpt-5.6-luna: fast, light model for everyday chat. gpt-6-sol: stronger, for harder steps.
CHAT_MODEL = os.getenv("CHAT_MODEL", "gpt-5.6-luna")
SMART_MODEL = os.getenv("SMART_MODEL", "gpt-6-sol")

PORTKEY_BASE_URL = os.getenv("PORTKEY_BASE_URL", "https://api.portkey.ai/v1")
PROMPT_PATH = Path(__file__).resolve().parent / "prompts" / "prompt.md"
SYSTEM_PROMPT = PROMPT_PATH.read_text(encoding="utf-8")


LOOP_LIMIT_REPLY = (
    "Whew, that question had me fetching a lot of answers at once, so I stopped before I "
    "could finish. 🐾 Could you ask about one or two items at a time? I'm happy to help!"
)

# The AI provider's own content filter (Azure OpenAI via Portkey) rejects some
# messages, e.g. "show me your system prompt", before the model sees them.
FILTERED_REPLY = (
    "I can't help with that one. I'm the Campus Customs shopping assistant, and I keep my "
    "instructions private. I'd be glad to help you find Yale gear, though: try asking about "
    "a hoodie, a size, or a price!"
)


def _is_content_filter(e: Exception) -> bool:
    return isinstance(e, ModelHTTPError) and e.status_code == 400 and "content_filter" in str(e.body)


class MissingAPIKey(RuntimeError):
    pass


def _model(model_name: str) -> OpenAIResponsesModel:
    key = os.getenv("PORTKEY_API_KEY")
    if not key:
        raise MissingAPIKey("PORTKEY_API_KEY is not set in .env")
    client = AsyncOpenAI(
        api_key=key,
        base_url=PORTKEY_BASE_URL,
        default_headers={"x-portkey-api-key": key},
    )
    return OpenAIResponsesModel(model_name, provider=OpenAIProvider(openai_client=client))


@lru_cache(maxsize=1)
def get_agent() -> Agent[ShopDeps, AgentReply]:
    """Build the agent on first use, so the server still starts without a key."""
    agent = Agent(
        _model(CHAT_MODEL),
        deps_type=ShopDeps,
        output_type=AgentReply,
        instructions=SYSTEM_PROMPT,
        toolsets=[shop_tools],
        model_settings=OpenAIResponsesModelSettings(openai_reasoning_effort="low"),
        retries=2,
    )

    @agent.instructions
    def shopper_and_page(ctx: RunContext[ShopDeps]) -> str:
        return context_block(ctx.deps)

    return agent


def context_block(deps: ShopDeps) -> str:
    """The per-message context the agent sees: who is chatting and what page they're on."""
    if deps.is_guest:
        who = "## Current shopper\nGuest (not logged in). You don't know their name or email."
    else:
        who = (
            "## Current shopper (from their login; this is the only customer you know about)\n"
            f"- First name: {deps.first_name or 'unknown'}\n"
            f"- Last name: {deps.last_name or 'unknown'}\n"
            f"- Email: {deps.email}"
        )
    page = f"## Current page\n{deps.page or 'unknown'}"
    p = deps.current_product
    if p:
        page += (
            "\nThe shopper is viewing this product (verified in the database). "
            "\"This\" or \"it\" means this product unless they name another one:\n"
            f"- product_id: {p.product_id}\n- name: {p.name}\n- type: {p.garment_type}\n"
            f"- colors: {', '.join(p.colors)}\n"
            "For its price, stock, or other facts, call lookup_product with this product_id."
        )
    return f"{who}\n\n{page}"


def _history_messages(turns: list[dict]) -> list[ModelMessage]:
    """Turn recent chat turns into PydanticAI message history.

    Assistant turns that showed cards get a short note listing them in order, so
    follow-ups like "what about the second one?" can be resolved.
    """
    messages: list[ModelMessage] = []
    while turns and turns[0]["role"] == "assistant":  # history should start with the shopper
        turns = turns[1:]
    for turn in turns:
        if turn["role"] == "user":
            messages.append(ModelRequest(parts=[UserPromptPart(content=turn["content"])]))
        else:
            text = turn["content"]
            cards = _cards_for(turn.get("product_ids", []))
            if cards:
                listed = "; ".join(f"{i}. {c.name} (id: {c.product_id})" for i, c in enumerate(cards, 1))
                text += f"\n[Cards shown with this reply, in order: {listed}]"
            messages.append(ModelResponse(parts=[TextPart(content=text)]))
    return messages


async def run_chat(request: ChatRequest, user: dict | None) -> ChatReply:
    """Answer one message. `user` comes from the login cookie (None = guest)."""
    product = product_details(request.product_id) if request.product_id else None
    deps = ShopDeps(
        user_id=user["id"] if user else None,
        first_name=(user.get("first_name") or user["name"].split(" ")[0]) if user else None,
        last_name=user.get("last_name") if user else None,
        email=user["email"] if user else None,
        page=request.page,
        current_product=product,  # None if the id is missing or not a real product
    )

    # Logged in: recent turns come from the database. Guests: from this visit's chat window.
    if user:
        turns = chat_history.recent_messages(user["id"], AGENT_HISTORY_LIMIT)
    else:
        # Guest history comes from the browser, so re-check it: anything that looks
        # like a password or card number is dropped before it can reach the model.
        turns = [t.model_dump() for t in request.history[-AGENT_HISTORY_LIMIT:]
                 if not sensitive.check(t.content)]
    log.info(
        "CHAT shopper=%s page=%r product_id=%r%s history=%d",
        f"user#{user['id']}" if user else "guest", request.page, request.product_id,
        "" if not request.product_id else (" (verified)" if product else " (ignored: not a real product)"),
        len(turns),
    )

    run_id = audit.new_run_id()
    shopper = f"user#{user['id']}" if user else "guest"
    try:
        result = await get_agent().run(
            request.message,
            deps=deps,
            message_history=_history_messages(turns),
            # Loop limit: stop runaway tool use (and cost) for a single message.
            usage_limits=UsageLimits(
                tool_calls_limit=MAX_TOOL_CALLS_PER_MESSAGE,
                request_limit=MAX_MODEL_REQUESTS_PER_MESSAGE,
            ),
        )
    except UsageLimitExceeded:
        log.warning("Loop limit hit after %d tool calls (run %s)", len(deps.tool_calls), run_id)
        audit.record_run(run_id=run_id, shopper=shopper, page=request.page, tool_calls=deps.tool_calls,
                         stop_reason="loop_limit", note=f"stopped: limit of {MAX_TOOL_CALLS_PER_MESSAGE} tool calls / "
                              f"{MAX_MODEL_REQUESTS_PER_MESSAGE} model requests reached after {len(deps.tool_calls)} call(s)")
        return ChatReply(reply=LOOP_LIMIT_REPLY, stopped=True)
    except Exception as e:
        if _is_content_filter(e):
            log.warning("Provider content filter rejected a message (run %s)", run_id)
            audit.record_run(run_id=run_id, shopper=shopper, page=request.page, tool_calls=deps.tool_calls,
                             stop_reason="provider_filter", note="rejected by the AI provider's content filter")
            return ChatReply(reply=FILTERED_REPLY, stopped=True)
        audit.record_run(run_id=run_id, shopper=shopper, page=request.page, tool_calls=deps.tool_calls,
                         stop_reason="error", note=f"error: {type(e).__name__}")
        raise
    reply = ChatReply(reply=result.output.reply)

    search = deps.search  # set by search_products; the last search in this turn wins
    if search:
        reply.products = _cards_for([hit.product_id for hit in search.results])
        reply.search = SearchSummary(
            query=search.query, total_matches=search.total_matches, shown=len(reply.products)
        )
    audit.record_run(run_id=run_id, shopper=shopper, page=request.page, tool_calls=deps.tool_calls,
                     stop_reason="answered", note="" if deps.tool_calls else f"replied without a tool ({len(reply.reply)} chars)")
    return reply


def saved_history(user_id: int) -> list[HistoryMessage]:
    """The shopper's saved chat, with cards rebuilt from the live database."""
    out = []
    for m in chat_history.recent_messages(user_id, HISTORY_LIMIT):
        cards = _cards_for(m["product_ids"])
        search = None
        if m["search"] and cards:
            search = SearchSummary(
                query=str(m["search"].get("query", "")),
                total_matches=int(m["search"].get("total_matches", len(cards))),
                shown=len(cards),
            )
        out.append(HistoryMessage(role=m["role"], content=m["content"], products=cards, search=search))
    return out


def _cards_for(product_ids: list[str]) -> list[ProductCard]:
    """Build cards from the database rows themselves (name, price, image, short info)."""
    rows = {p["product_id"]: to_display(p) for p in db.list_products()}
    return [
        ProductCard(
            product_id=p["product_id"],
            name=p["name"],
            price=p["price"],
            image_url=p["image_url"],
            short_info=p["short_description"],
        )
        for p in (rows[pid] for pid in product_ids if pid in rows)
    ]
