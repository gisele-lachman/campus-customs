"""Campus Customs backend.

Run from inside the backend folder:
    uvicorn main:app --reload --port 8000
"""

import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

import db
import audit
import chat_history
import sensitive
from agent import _cards_for, run_chat, saved_history
from auth import current_user
from auth import router as auth_router
from display import to_display
from models import ChatReply, ChatRequest, HistoryMessage, ProductCard, SearchSummary
from tools import search_catalogue

log = logging.getLogger("uvicorn.error")  # shows up in the server output
app = FastAPI(title="Campus Customs API")

# The Vite dev server proxies /api and /images here, but allow it directly too.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Product pictures from data/products, e.g. /images/basic-hoodie-big-yale.jpg
app.mount("/images", StaticFiles(directory=db.IMAGES_DIR), name="images")

# Create account, log in, log out, and "who am I" (see auth.py).
app.include_router(auth_router)


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/api/products")
def list_products() -> list[dict]:
    return [to_display(p) for p in db.list_products()]


@app.get("/api/products/{product_id}")
def get_product(product_id: str) -> dict:
    product = db.get_product(product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return to_display(product)


@app.get("/api/search")
def search(q: str) -> dict:
    """Browse search for the website (e.g. "Shop by college" on the Home page).

    Same matching as the chatbot's search_products tool; cards built from database rows.
    """
    result = search_catalogue(q[:100])
    cards: list[ProductCard] = _cards_for([h.product_id for h in result.results])
    summary = SearchSummary(query=q[:100], total_matches=result.total_matches, shown=len(cards))
    return {"search": summary, "products": cards}


@app.post("/api/chat")
async def chat(body: ChatRequest, request: Request) -> ChatReply:
    """Send the shopper's message to the agent. Works logged in or out.

    Who is chatting comes only from the login cookie, never from the request body.
    """
    # Sensitive-info guard: passwords and card numbers never reach the model, the
    # database, or the logs. Only the kind of match is logged, never the text.
    kind = sensitive.check(body.message)
    if kind:
        log.info("GUARD blocked a chat message (looked like a %s); not sent to the model or saved", kind)
        user = current_user(request)
        audit.record_run(run_id=audit.new_run_id(), shopper=f"user#{user['id']}" if user else "guest",
                         page=body.page, tool_calls=[], stop_reason="blocked_sensitive",
                         note=f"message blocked (looked like a {kind}); model not called")
        return ChatReply(reply=sensitive.WARNING, blocked=True)

    user = current_user(request)
    try:
        reply = await run_chat(body, user)
    except Exception as e:
        # Log only the error type, never details that could contain a key.
        log.error("Chat failed: %s", type(e).__name__)
        raise HTTPException(
            status_code=503,
            detail="Sorry, the shopping assistant is having trouble right now. Please try again in a moment.",
        )
    if user and not reply.stopped:  # guests: nothing is saved
        try:
            chat_history.save_exchange(
                user["id"], body.message, reply.reply,
                [p.product_id for p in reply.products],
                {"query": reply.search.query, "total_matches": reply.search.total_matches} if reply.search else None,
            )
        except Exception as e:
            log.error("Saving chat failed: %s", type(e).__name__)
    return reply


@app.get("/api/chat/history")
def get_chat_history(request: Request) -> list[HistoryMessage]:
    """The logged-in shopper's own saved chat (empty for guests)."""
    user = current_user(request)
    return saved_history(user["id"]) if user else []


@app.delete("/api/chat/history")
def clear_chat_history(request: Request) -> dict:
    """Delete only the logged-in shopper's own chat history."""
    user = current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Please log in to clear saved chat history.")
    return {"deleted": chat_history.clear_history(user["id"])}
