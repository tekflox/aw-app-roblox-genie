"""Config/secret resolvers for this app.

Same split as aw-app-roblox (and aw-google-maps/aw-app-notion before it):
plain, non-sensitive knobs ride the generic ``config_schema`` path
(``ctx.config``); the real credential (the roblox-pilot-backend API key)
goes to ``ctx.secrets`` instead, via this app's own ``POST /settings``.

Resolved through callables, not read once at ``activate()`` time: a value
saved in Settings must take effect on the very next tool call, no restart.
"""
from __future__ import annotations

from typing import Callable

_config: Callable[[], dict] = lambda: {}
_secret: Callable[[str], str | None] = lambda name: None

DEFAULT_PILOT_BACKEND_URL = "https://roblox-pilot-backend.app.aw.tekflox.com"

PILOT_BACKEND_API_KEY = "roblox_pilot_backend_api_key"


def install_resolvers(config_fn: Callable[[], dict], secret_fn: Callable[[str], str | None]) -> None:
    """Called once from ``plugin.activate()``."""
    global _config, _secret
    _config = config_fn
    _secret = secret_fn


def _cfg() -> dict:
    try:
        return _config() or {}
    except Exception:
        return {}


def pilot_backend_url() -> str:
    return (_cfg().get("roblox_pilot_backend_url") or DEFAULT_PILOT_BACKEND_URL).rstrip("/")


def pilot_backend_api_key() -> str:
    return (_secret(PILOT_BACKEND_API_KEY) or "").strip()
