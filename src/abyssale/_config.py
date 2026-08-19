"""Settings resolution: explicit argument, then environment variable, then default.

The Node SDK reads the environment once at *import* time and throws if the key is missing. That
does not port: a module that explodes on import is hostile in Python, and it makes a second key (a
second workspace) unrepresentable. Here, config is per-client and resolved in the constructor.
"""

from __future__ import annotations

import os

from ._errors import AbyssaleConfigError

DEFAULT_BASE_URL = "https://api.abyssale.com"
DEFAULT_TIMEOUT_SECONDS = 30.0
DEFAULT_MAX_RETRIES = 3

ENV_API_KEY = "ABYSSALE_API_KEY"
ENV_BASE_URL = "ABYSSALE_BASE_URL"
ENV_TIMEOUT_MS = "ABYSSALE_TIMEOUT_MS"
ENV_MAX_RETRIES = "ABYSSALE_MAX_RETRIES"


def resolve_api_key(api_key: str | None) -> str:
    key = api_key or os.environ.get(ENV_API_KEY)
    if not key:
        raise AbyssaleConfigError(
            f"[abyssale] No API key. Pass api_key=... or set the {ENV_API_KEY} environment variable."
        )
    return key


def resolve_base_url(base_url: str | None) -> str:
    # `ABYSSALE_BASE_URL` is an escape hatch for pointing the SDK at a local edge; it is not part of
    # the documented surface.
    return (base_url or os.environ.get(ENV_BASE_URL) or DEFAULT_BASE_URL).rstrip("/")


def resolve_timeout(timeout: float | None) -> float:
    """Timeout in **seconds**. The env var is in milliseconds, for parity with the Node SDK."""
    if timeout is not None:
        if timeout <= 0:
            raise AbyssaleConfigError(f"[abyssale] timeout must be a positive number of seconds, got {timeout!r}")
        return float(timeout)
    raw = os.environ.get(ENV_TIMEOUT_MS)
    if not raw:
        return DEFAULT_TIMEOUT_SECONDS
    try:
        value = float(raw)
    except ValueError as err:
        raise AbyssaleConfigError(f"[abyssale] {ENV_TIMEOUT_MS} must be a positive number, got {raw!r}") from err
    if value <= 0:
        raise AbyssaleConfigError(f"[abyssale] {ENV_TIMEOUT_MS} must be a positive number, got {raw!r}")
    return value / 1000.0


def resolve_max_retries(max_retries: int | None) -> int:
    if max_retries is not None:
        if max_retries < 0:
            raise AbyssaleConfigError(f"[abyssale] max_retries must be a non-negative integer, got {max_retries!r}")
        return int(max_retries)
    raw = os.environ.get(ENV_MAX_RETRIES)
    if not raw:
        return DEFAULT_MAX_RETRIES
    try:
        value = int(raw)
    except ValueError as err:
        raise AbyssaleConfigError(f"[abyssale] {ENV_MAX_RETRIES} must be a non-negative integer, got {raw!r}") from err
    if value < 0:
        raise AbyssaleConfigError(f"[abyssale] {ENV_MAX_RETRIES} must be a non-negative integer, got {raw!r}")
    return value
