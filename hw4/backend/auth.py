"""Login sessions and the /api/auth routes.

After a successful login the backend sets a signed, HttpOnly cookie holding only
the user's id. JavaScript can't read it, and it can't be forged without the
SESSION_SECRET from .env. Refreshing the page keeps you logged in until it expires.
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, Request, Response
from itsdangerous import BadSignature, URLSafeTimedSerializer
from pydantic import BaseModel

import users

load_dotenv(Path(__file__).resolve().parent.parent / ".env")
SECRET = os.environ.get("SESSION_SECRET")
if not SECRET:
    raise RuntimeError("SESSION_SECRET is missing. Copy .env.example to .env and set it.")

COOKIE_NAME = "cc_session"
MAX_AGE_SECONDS = 7 * 24 * 60 * 60  # one week
COOKIE_SECURE = os.environ.get("COOKIE_SECURE", "false").lower() == "true"

_signer = URLSafeTimedSerializer(SECRET, salt="campus-customs-login")
router = APIRouter(prefix="/api/auth", tags=["auth"])


class SignupBody(BaseModel):
    first_name: str
    last_name: str
    email: str
    password: str
    confirm_password: str


class LoginBody(BaseModel):
    email: str
    password: str


def _start_session(response: Response, user_id: int) -> None:
    response.set_cookie(
        COOKIE_NAME,
        _signer.dumps({"uid": user_id}),
        max_age=MAX_AGE_SECONDS,
        httponly=True,
        samesite="lax",
        secure=COOKIE_SECURE,
        path="/",
    )


def current_user(request: Request) -> dict | None:
    """The logged-in user (without password hash), or None. Reusable by other routes."""
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        return None
    try:
        data = _signer.loads(token, max_age=MAX_AGE_SECONDS)
    except BadSignature:
        return None
    return users.get_user(data.get("uid"))


@router.post("/signup")
def signup(body: SignupBody, response: Response) -> dict:
    try:
        user = users.create_user(
            body.first_name, body.last_name, body.email, body.password, body.confirm_password
        )
    except users.SignupError as e:
        raise HTTPException(status_code=400, detail=str(e))
    _start_session(response, user["id"])
    return user


@router.post("/login")
def login(body: LoginBody, response: Response) -> dict:
    user = users.authenticate(body.email, body.password)
    if user is None:
        raise HTTPException(status_code=401, detail="Incorrect email or password.")
    _start_session(response, user["id"])
    return user


@router.post("/logout")
def logout(response: Response) -> dict:
    response.delete_cookie(COOKIE_NAME, path="/")
    return {"ok": True}


@router.get("/me")
def me(request: Request) -> dict | None:
    return current_user(request)
