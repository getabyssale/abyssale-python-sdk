"""Retry classification — a port of ``abyssale-nodejs-sdk/src/middleware.ts``.

Transport-free on purpose: the sync client, the async client and both polling loops all call
:func:`plan_retry`, so the rules cannot drift between them. They already had, once, in the Node SDK.

None of the ``AbortSignal`` / ``WeakMap`` / ``request.clone()`` apparatus from the TypeScript
version is needed here. All of it existed because ``fetch`` consumes a request's body stream, so a
retried POST could not be re-dispatched; an ``httpx.Request`` is re-dispatchable as many times as
you like.
"""

from __future__ import annotations

import email.utils
import random
import time
from collections.abc import Generator
from typing import Any, NamedTuple

#: 5xx: the request may or may not have been processed — only safe to repeat if it is idempotent.
RETRYABLE_SERVER_STATUSES = (500, 502, 503, 504)

#: Methods that can be repeated without creating anything twice. Every POST on this API either
#: generates an asset, queues a batch or duplicates a template — all of which consume credits, so
#: none of them are repeated automatically. A 504 at the gateway does NOT mean the generation did
#: not happen.
IDEMPOTENT_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})

#: How long to wait before the single probe a bare 429 is given. See :func:`plan_retry`.
#:
#: Sized against the thing it is probing for: the global ceiling is 10 requests per **second**, so
#: one second is the shortest wait that reliably clears it, and waiting longer only lengthens the
#: failure when the refusal turns out to be permanent.
CEILING_PROBE_DELAY_SECONDS = 1.0

#: Error ids that answer 429 and are known to be permanent for this key, so not even the probe
#: below is worth spending.
#:
#: ``rate_limit_exceeded`` is deliberately NOT here even though it is permanent when it means "out
#: of credits" — see :func:`plan_retry` for why it cannot be classified from the id alone.
PERMANENT_429_CODES = frozenset({"feature_not_in_plan"})


class RetryPlan(NamedTuple):
    """How a response should be re-attempted."""

    #: True = exactly one attempt, whatever ``max_retries`` says. See :func:`plan_retry`.
    probe: bool
    #: Fixed wait in seconds before the first attempt; ``None`` means use the exponential schedule.
    delay: float | None


def retry_after_seconds(response: Any) -> float | None:
    """``Retry-After`` in seconds — the header is either delta-seconds or an HTTP date.

    Returns ``None`` when absent or unparseable.
    """
    raw = response.headers.get("retry-after") if response is not None else None
    if not raw:
        return None
    try:
        return max(0.0, float(raw))
    except (TypeError, ValueError):
        pass
    try:
        parsed = email.utils.parsedate_to_datetime(raw)
    except (TypeError, ValueError):
        return None
    if parsed is None:
        return None
    return max(0.0, parsed.timestamp() - time.time())


def read_error_id(response: Any) -> str | None:
    """The ``id`` from an error envelope, or ``None`` if the body is absent or not the envelope."""
    try:
        body = response.json()
    except Exception:
        return None
    return body["id"] if isinstance(body, dict) and isinstance(body.get("id"), str) else None


def plan_retry(response: Any, error_id: str | None = None) -> RetryPlan | None:
    """Whether a response is worth asking for again, ignoring the request method.

    The single derivation of that question, used by the request loop and by the polling helpers.
    Anything method-sensitive (a 5xx on a POST) stays with the caller — a poll is always a GET, so
    only the request loop has that concern.

    429 is the hard case, because **three unrelated refusals share the status and two of them share
    an id**:

    - ``request_rate_limited`` — the per-workspace endpoint budget. The edge sends ``Retry-After``
      alongside it, so it is unambiguous and gets the full retry ladder.
    - ``feature_not_in_plan`` — your plan excludes this design type. Permanent; never retried.
    - ``rate_limit_exceeded`` — **two different things under one id.** Either the plan's credits are
      spent (permanent), or the gateway's global 10 req/s ceiling was hit (clears in under a
      second). Only ``message`` distinguishes them, and the ceiling is enforced at the GATEWAY, one
      layer above the edge, so its response carries neither ``Retry-After`` nor reliably the edge's
      envelope at all.

    That last case is why a bare 429 is not simply fatal. Treating it as permanent means a burst of
    parallel generation calls fails outright, and generation endpoints are in no rate-limit tier, so
    the ceiling is the ONLY limit they can hit. Treating it as fully retryable spends ~7s of backoff
    on refusals that never clear.

    So it gets exactly **one** probe after a fixed second. Being wrong costs one second on a call
    that was failing anyway; being right rescues a call that would otherwise have failed outright.
    That asymmetry, not a confident classification, is the argument.
    """
    if response.status_code in RETRYABLE_SERVER_STATUSES:
        return RetryPlan(probe=False, delay=retry_after_seconds(response))
    if response.status_code != 429:
        return None

    after = retry_after_seconds(response)
    # It told us when to come back, so it is a real throttle and we believe it.
    if after is not None:
        return RetryPlan(probe=False, delay=after)
    if error_id and error_id in PERMANENT_429_CODES:
        return None
    return RetryPlan(probe=True, delay=CEILING_PROBE_DELAY_SECONDS)


def is_retryable_for_method(response: Any, method: str) -> bool:
    """Method-sensitive half of the rule: a 5xx on a write may already have been processed."""
    if response.status_code in RETRYABLE_SERVER_STATUSES:
        return method.upper() in IDEMPOTENT_METHODS
    return True


def backoff_delay(attempt: int) -> float:
    """Exponential backoff with jitter: 1s, 2s, 4s … plus up to 100ms."""
    return float(2 ** (attempt - 1)) + random.random() * 0.1


def _plan_for(response: Any) -> RetryPlan | None:
    # The body is only read for a bare 429, where the id can rule the retry out entirely.
    return plan_retry(response, read_error_id(response) if response.status_code == 429 else None)


def retry_schedule(response: Any, method: str, max_retries: int) -> Generator[float, Any, None]:
    """The retry schedule for one request, as a generator of delays in seconds.

    Shared by the sync and the async client so the two cannot drift; each ``send`` the caller makes
    hands the new response back in, and the generator decides whether there is another attempt::

        schedule = retry_schedule(response, "GET", max_retries)
        delay = next(schedule, None)
        while delay is not None:
            sleep(delay)
            response = send()
            delay = schedule.send(response)   # StopIteration -> done

    It stops on the last allowed attempt without classifying that response — whatever came back is
    what the caller gets — and stops early on a success, a verdict, or a bare 429 whose probe was
    the attempt just made.
    """
    plan = _plan_for(response)
    if plan is None or not is_retryable_for_method(response, method):
        return
    attempts = attempts_for(plan, max_retries)
    after = plan.delay

    for attempt in range(1, attempts + 1):
        latest = yield (after if after is not None else backoff_delay(attempt))
        if attempt == attempts:
            return
        plan = _plan_for(latest)
        if plan is None or plan.probe:
            return
        after = plan.delay


def attempts_for(plan: RetryPlan, max_retries: int) -> int:
    """How many retries a plan is allowed.

    A probe is one attempt by definition — it exists to find out whether the refusal clears, not to
    wait one out, so it does not scale with ``max_retries``. It is still CAPPED by it:
    ``max_retries=0`` means retries are off, and a probe is a retry.
    """
    return min(1, max_retries) if plan.probe else max_retries
