"""Verify the signature on an inbound Abyssale webhook delivery.

A **public** module — the only one besides ``abyssale`` and ``abyssale.models`` — and deliberately
standalone: it imports nothing from the clients, so a receiver process can

    from abyssale.webhooks import verify_webhook_signature

without pulling in ``httpx`` or anything that resolves an API key. Verifying a delivery is not an
API call and must not need a credential that can spend credits.

Transport-free and clock-injectable for the same reason ``_retry`` is: the whole module is one pure
function plus a parser, so the rules cannot drift and a test needs no fixtures.
"""

from __future__ import annotations

import hashlib
import hmac
import re
import time

#: Purpose label bound into the signed bytes, so a signature minted for a webhook can never be
#: replayed against another signed surface (dynamic image URLs use a different label).
SIGNATURE_PREFIX = "v1:webhook:"

#: How far a delivery's ``t`` may drift from now, in seconds.
#:
#: Generous enough for clock skew and a slow queue, short enough that a delivery captured off the
#: wire cannot be replayed indefinitely. Abyssale's own retry ladder spans hours, so a retry can
#: legitimately arrive well outside this window — that is what ``X-Abyssale-Delivery-Id`` is for.
DEFAULT_TOLERANCE_SECONDS = 300

#: `t` is plain digits. `int()` alone would accept ``" 12"``, ``"+12"`` and ``"12_000"``.
_DIGITS = re.compile(r"\A\d+\Z")


def _parse(header: str) -> list[tuple[str, str]]:
    """``t=1,v1=ab,v1=cd`` → ``[("t", "1"), ("v1", "ab"), ("v1", "cd")]``, dropping junk.

    Not a dict: a rotation puts **two** ``v1`` entries in the header and a mapping would keep only
    one of them.
    """
    pairs = []
    for part in header.split(","):
        key, _, value = part.partition("=")
        if _:
            pairs.append((key.strip(), value.strip()))
    return pairs


def verify_webhook_signature(
    body: bytes | str,
    header: str | None,
    secret: str,
    *,
    tolerance_seconds: int = DEFAULT_TOLERANCE_SECONDS,
    now: float | None = None,
) -> bool:
    """``True`` when *body* was signed by Abyssale with *secret* and is inside the freshness window.

    Never raises. Every malformed, absent or hostile header is simply ``False``, because anyone who
    can reach a webhook URL can send one and an exception in a handler is a 500 — plus, on most
    frameworks, a retried delivery.

    Parameters
    ----------
    body:
        The **raw** request body, exactly as received. Parsing the JSON and re-serialising it
        reorders keys and changes spacing, so the signature will not match. In Flask use
        ``request.get_data()``; in FastAPI ``await request.body()``; in Django
        ``request.body``. Never ``json.dumps(request.json)``.
    header:
        The ``X-Abyssale-Signature`` value, or ``None`` if absent.
    secret:
        The workspace's signing secret from ``GET /signing-secret``
        (:meth:`abyssale.Abyssale.get_signing_secret`).
    tolerance_seconds:
        Maximum drift between the delivery's ``t`` and *now*. Defaults to 300.
    now:
        Current Unix time, injected for tests. Defaults to the system clock.

    Example
    -------
    ::

        from abyssale.webhooks import verify_webhook_signature

        @app.post("/webhooks/abyssale")
        def receive():
            if not verify_webhook_signature(
                request.get_data(), request.headers.get("X-Abyssale-Signature"), SECRET
            ):
                return "", 401
            ...

    Note
    ----
    For 24 hours after a rotation a delivery carries **two** ``v1`` values, one per valid secret,
    and only one matches the secret you hold — which is what lets you deploy a rotated secret on
    your own schedule. Every ``v1`` is therefore checked, and a single non-matching one never means
    "invalid".
    """
    if not header or not secret:
        return False

    pairs = _parse(header)

    timestamps = [value for key, value in pairs if key == "t"]
    if not timestamps or not _DIGITS.match(timestamps[0]):
        return False

    timestamp = int(timestamps[0])
    if abs((time.time() if now is None else now) - timestamp) > tolerance_seconds:
        return False

    if isinstance(body, str):
        body = body.encode("utf-8")

    expected = hmac.new(
        secret.encode("utf-8"),
        f"{SIGNATURE_PREFIX}{timestamp}.".encode() + body,
        hashlib.sha256,
    ).hexdigest()

    # `isascii()` before comparing: `hmac.compare_digest` RAISES on a `str` containing a non-ASCII
    # character, and `v1` is attacker-controlled, so a hostile header would take the handler down
    # instead of being rejected. `expected` is always hexdigest, so only the candidate needs it.
    return any(value.isascii() and hmac.compare_digest(expected, value) for key, value in pairs if key == "v1")


def signature_timestamp(header: str | None) -> int | None:
    """The delivery's ``t`` in Unix seconds, or ``None`` if absent or malformed.

    ``t`` is the only trustworthy time in a delivery — it is covered by the signature, whereas
    anything inside the payload was rebuilt at send time. Use it to reject stale deliveries, never
    to order them: a retry of an older event can arrive after a newer one. Deduplicate on
    ``X-Abyssale-Delivery-Id``, which is stable across every attempt while ``t`` is not.
    """
    if not header:
        return None

    for key, value in _parse(header):
        if key == "t" and _DIGITS.match(value):
            return int(value)

    return None
