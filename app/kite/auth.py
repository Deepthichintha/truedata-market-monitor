"""Kite Connect login helpers for the provider-evaluation environment.

The API secret is used only server-side. The browser receives the Kite login
redirect and returns with a short-lived request_token, which is exchanged for
an access token by this module.
"""

from dataclasses import dataclass

from kiteconnect import KiteConnect

from app.kite.config import KITE_API_KEY, KITE_API_SECRET, KITE_REDIRECT_URL


@dataclass
class KiteSession:
    access_token: str
    user_id: str | None = None


_access_token: str = ""
_user_id: str | None = None


def configured() -> bool:
    return bool(KITE_API_KEY and KITE_API_SECRET)


def login_url() -> str:
    if not KITE_API_KEY:
        raise RuntimeError("KITE_API_KEY is not configured")
    kite = KiteConnect(api_key=KITE_API_KEY)
    return kite.login_url()


def exchange_request_token(request_token: str) -> KiteSession:
    global _access_token, _user_id

    if not configured():
        raise RuntimeError("KITE_API_KEY and KITE_API_SECRET must be configured")

    kite = KiteConnect(api_key=KITE_API_KEY)
    session = kite.generate_session(
        request_token,
        api_secret=KITE_API_SECRET,
    )
    _access_token = session["access_token"]
    _user_id = session.get("user_id")
    return KiteSession(access_token=_access_token, user_id=_user_id)


def get_access_token() -> str:
    return _access_token


def set_access_token(token: str) -> None:
    global _access_token
    _access_token = token.strip()


def auth_status() -> dict:
    token = _access_token
    return {
        "configured": configured(),
        "authenticated": bool(token),
        "user_id": _user_id,
        # Never return the token itself to the frontend.
    }


def redirect_url() -> str:
    return KITE_REDIRECT_URL
