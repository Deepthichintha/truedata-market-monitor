"""Kite Connect authentication helpers for provider evaluation.

The API secret is used only server-side. Kite's developer-console redirect URL
is authoritative: ``KITE_REDIRECT_URL`` documents the callback this deployment
expects, but it cannot override the redirect URL registered against the Kite
API key.
"""

from dataclasses import dataclass
from urllib.parse import urlencode

from kiteconnect import KiteConnect

from app.kite.config import (
    KITE_API_KEY,
    KITE_API_SECRET,
    KITE_ACCESS_TOKEN,
    KITE_REDIRECT_URL,
)


@dataclass
class KiteSession:
    access_token: str
    user_id: str | None = None


_access_token: str = ""
_user_id: str | None = None


def configured() -> bool:
    return bool(KITE_API_KEY and KITE_API_SECRET)


def login_url() -> str:
    """Return the official Kite login URL.

    Kite determines the actual post-login redirect from the redirect URL
    registered for this API key in the Kite developer console. We add a small
    redirect parameter only for traceability; it does not change the registered
    redirect target.
    """
    if not KITE_API_KEY:
        raise RuntimeError("KITE_API_KEY is not configured")

    kite = KiteConnect(api_key=KITE_API_KEY)
    url = kite.login_url()
    separator = "&" if "?" in url else "?"
    return url + separator + urlencode({"redirect_params": "provider=kite"})


def exchange_request_token(request_token: str) -> KiteSession:
    """Exchange Kite's short-lived request token for the daily access token."""
    global _access_token, _user_id

    if not configured():
        raise RuntimeError("KITE_API_KEY and KITE_API_SECRET must be configured")

    request_token = request_token.strip()
    if not request_token:
        raise RuntimeError("Kite request_token is empty")

    kite = KiteConnect(api_key=KITE_API_KEY)
    session = kite.generate_session(
        request_token,
        api_secret=KITE_API_SECRET,
    )
    _access_token = session["access_token"]
    _user_id = session.get("user_id")
    return KiteSession(access_token=_access_token, user_id=_user_id)


def get_access_token() -> str:
    """Return the live-session token, falling back to an explicitly configured token."""
    return _access_token or KITE_ACCESS_TOKEN.strip()


def set_access_token(token: str) -> None:
    global _access_token
    _access_token = token.strip()


def auth_status() -> dict:
    token = get_access_token()
    return {
        "configured": configured(),
        "authenticated": bool(token),
        "user_id": _user_id,
        "source": "session" if _access_token else ("environment" if token else None),
        "redirect_url_expected": KITE_REDIRECT_URL,
        # Never return the token itself to the frontend.
    }


def redirect_url() -> str:
    return KITE_REDIRECT_URL
