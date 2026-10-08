# Campus Customs: a Yale merch shop with an AI shopping assistant

A vintage-varsity storefront (React + Vite) with a FastAPI backend. The site has a PydanticAI chatbot, "the Campus Customs Bulldog", that answers price, stock, search, and comparison questions from the shop database. How it all works is in [`output/harness.md`](output/harness.md).

## 1. Add the data pack (not in this repo)
The database and product pictures are private, so they aren't committed. Put them here:

```
hw4/data/campus_customs.db
hw4/data/products/        (the .jpg product images)
```

## 2. Set up `.env`
Copy the example file and fill it in (in the `hw4` folder):

```bash
cp .env.example .env
```

- `PORTKEY_API_KEY`: your Portkey key (AI calls go to OpenAI through Portkey).
- `SESSION_SECRET`: any long random string. You can make one with:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(48))"
```

Everything else is optional. The models default to `gpt-5.6-luna` (chat) and `gpt-6-sol` (smart).

## 3. Install packages
Python 3 (from `hw4`):

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
```

Node.js (from `hw4`):

```bash
cd frontend && npm install
```

## 4. Start the backend (port 8000)

```bash
cd backend && ../.venv/bin/uvicorn main:app --reload --port 8000
```

(With the virtual environment activated, `uvicorn main:app --reload --port 8000` from `backend/` works too.)

## 5. Start the front end (port 5173), in a second terminal

```bash
cd frontend && npm run dev
```

Open **http://localhost:5173**. The front end forwards `/api` and `/images` to the backend on port 8000.

## Test login
- Email: `test@campuscustoms.yale.edu`
- Password: `password`

This is the seed test account from the data pack. You can also create your own account on the site.

## What's where
| Path | Contents |
|---|---|
| `backend/` | `main.py` (API routes), `agent.py`, `tools.py`, `models.py`, `prompts/prompt.md`, plus helpers: auth, database access, the sensitive-info guard, limits, and the audit trail |
| `frontend/` | The React app (`src/pages`, `src/components`, `src/chat`, `src/auth`) |
| `output/` | `harness.md` (how it works), `design.md`, `usability.md`, `app_check.html` (screenshot checks), `audit_trail.json` (agent audit log) |
| `AI_prompts.md` | The full log of prompts used to build this project |
