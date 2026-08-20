"""Settings resolution: explicit argument, then environment variable, then default.

Config is per-client and resolved in the constructor, not read once at import time: a module that
explodes on import is hostile in Python, and import-time config makes a second key — a second
workspace — unrepresentable.
"""

from __future__ import annotations

import math
import os

from ._errors import AbyssaleConfigError

DEFAULT_BASE_URL = "https://api.abyssale.com"
DEFAULT_TIMEOUT_SECONDS = 30.0
DEFAULT_MAX_RETRIES = 3

#: Longest ``Retry-After`` the SDK will sit out on the caller's behalf, in seconds.
#:
#: This API's rate limiter can name a very long cool-off once a quota is spent — cool-offs of
#: ~1700s have been observed — and ``max_retries`` multiplies it. Sleeping through that turns one
#: call into an hour of silence with no way to intervene, so past this bound the SDK stops retrying
#: and raises instead, with ``retry_after`` carrying the server's figure. Waiting longer than this
#: is a decision only the caller can make: a nightly batch may well want to, a request with a user
#: attached never does.
DEFAULT_MAX_RETRY_WAIT_SECONDS = 30.0

ENV_API_KEY = "ABYSSALE_API_KEY"
ENV_BASE_URL = "ABYSSALE_BASE_URL"
ENV_TIMEOUT_MS = "ABYSSALE_TIMEOUT_MS"
ENV_MAX_RETRIES = "ABYSSALE_MAX_RETRIES"
ENV_MAX_RETRY_WAIT_MS = "ABYSSALE_MAX_RETRY_WAIT_MS"


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
    """Timeout in **seconds**. The env var is in milliseconds, matching how the API documents
    its own millisecond fields (`next_check_after_ms`)."""
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


def resolve_max_retry_wait(max_retry_wait: float | None) -> float:
    """Cap on a single server-requested wait, in **seconds**. The env var is in milliseconds,
    matching ``timeout``.

    ``math.inf`` — as the argument, or ``inf`` in the env var — disables the cap and restores
    "sleep for as long as the server asks", which is what a batch job that wants to wait out a
    quota should pass.
    """
    if max_retry_wait is not None:
        if max_retry_wait <= 0 or math.isnan(max_retry_wait):
            raise AbyssaleConfigError(
                f"[abyssale] max_retry_wait must be a positive number of seconds (or math.inf to "
                f"disable the cap), got {max_retry_wait!r}"
            )
        return float(max_retry_wait)
    raw = os.environ.get(ENV_MAX_RETRY_WAIT_MS)
    if not raw:
        return DEFAULT_MAX_RETRY_WAIT_SECONDS
    try:
        value = float(raw)
    except ValueError as err:
        raise AbyssaleConfigError(
            f"[abyssale] {ENV_MAX_RETRY_WAIT_MS} must be a positive number or 'inf', got {raw!r}"
        ) from err
    if value <= 0 or math.isnan(value):
        raise AbyssaleConfigError(f"[abyssale] {ENV_MAX_RETRY_WAIT_MS} must be a positive number or 'inf', got {raw!r}")
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
