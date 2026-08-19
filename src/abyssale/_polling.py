"""The polling loop, minus the sleeping.

Drives the two status operations the spec documents as polling endpoints — ``getGenerationRequest``
and ``getDuplicationRequest`` — whose responses carry the terminal condition (``is_finalized``, and
``status`` reaching ``COMPLETED``/``ERROR``).

Everything here is transport-free so the sync and async ``wait_for_*`` helpers share one
implementation of the schedule, the transient-failure budget and the deadline; only the sleep
differs between them.
"""

from __future__ import annotations

import random
import time
from dataclasses import dataclass
from typing import TypeVar

from ._errors import AbyssaleAPIError, AbyssaleConnectionError, AbyssaleError, AbyssalePollingError
from ._retry import plan_retry

T = TypeVar("T")

DEFAULT_POLL_INTERVAL_SECONDS = 3.0
DEFAULT_POLL_MAX_INTERVAL_SECONDS = 30.0
DEFAULT_POLL_TIMEOUT_SECONDS = 1800.0  # 30 minutes

POLL_MIN_INTERVAL_SECONDS = 2.0
POLL_MIN_MAX_INTERVAL_SECONDS = 5.0
POLL_MIN_TIMEOUT_SECONDS = 60.0

#: How many *consecutive* transient failures a poll loop absorbs before giving up.
#:
#: A wait can legitimately run for the full 30 minutes — the async endpoint has no completion bound,
#: and an AI image round-trip pushes well past a plain render. Failing the whole wait on one 503 or
#: one dropped connection would throw away everything already elapsed for a condition that the next
#: poll, three seconds later, usually clears. The streak resets on any successful poll, so this
#: tolerates blips without hiding an endpoint that is actually down.
POLL_MAX_TRANSIENT_FAILURES = 3


@dataclass(frozen=True)
class PollOptions:
    """Resolved polling schedule, in seconds."""

    interval: float
    max_interval: float
    timeout: float


def resolve_poll_options(
    interval: float | None = None,
    max_interval: float | None = None,
    timeout: float | None = None,
) -> PollOptions:
    """Apply the defaults and the floors. A caller cannot poll faster than the floors allow."""
    return PollOptions(
        interval=max(interval if interval is not None else DEFAULT_POLL_INTERVAL_SECONDS, POLL_MIN_INTERVAL_SECONDS),
        max_interval=max(
            max_interval if max_interval is not None else DEFAULT_POLL_MAX_INTERVAL_SECONDS,
            POLL_MIN_MAX_INTERVAL_SECONDS,
        ),
        timeout=max(timeout if timeout is not None else DEFAULT_POLL_TIMEOUT_SECONDS, POLL_MIN_TIMEOUT_SECONDS),
    )


def _jitter() -> float:
    return random.random() * 0.5


class PollLoop:
    """The state of one ``wait_for_*`` call.

    Usage, in both the sync and the async client::

        loop = PollLoop(resolve_poll_options(...))
        while True:
            try:
                data = fetch()
            except AbyssaleError as err:
                loop.absorb(err)          # re-raises as AbyssalePollingError when fatal
            else:
                loop.succeeded()
                if is_done(data):
                    return data
            sleep(loop.next_wait())       # raises when the next wait would cross the deadline
    """

    def __init__(self, options: PollOptions) -> None:
        self._options = options
        self._deadline = time.monotonic() + options.timeout
        self._interval = options.interval
        self._transient_failures = 0
        #: How long the server asked us to wait, when the last failure said so. It replaces the
        #: backoff for exactly one wait: a throttle that says "60s" is not answered by re-asking in
        #: 3, which would spend the whole transient-failure budget inside the window it was told to
        #: sit out.
        self._server_requested_wait: float | None = None
        #: Bare 429s absorbed so far. Capped at one for the whole poll, not one in a row: the probe
        #: exists to find out whether the refusal was the gateway's per-second ceiling, and a second
        #: bare 429 after a successful probe answers that — it is not the ceiling, so waiting is not
        #: the fix. Without this cap a spent credit balance would be re-asked for the full 30
        #: minutes.
        self._ceiling_probes = 0

    def succeeded(self) -> None:
        self._transient_failures = 0
        self._server_requested_wait = None

    def absorb(self, err: AbyssaleError) -> None:
        """Swallow a failed poll if it is a blip, else re-raise it as an :class:`AbyssalePollingError`.

        A 5xx or a real throttle says nothing about the generation itself, while any other 4xx is a
        verdict — ``generation_request_not_found`` must fail on the first poll rather than be
        re-asked for 30 minutes. The classification is :func:`plan_retry`, the same one the request
        loop uses, so the two cannot drift into disagreeing about which 429 is worth re-asking.
        """
        if isinstance(err, AbyssaleAPIError):
            plan = plan_retry(err.response, err.id)
            if plan is None:
                raise self._fatal(err)
            if plan.probe:
                self._ceiling_probes += 1
                if self._ceiling_probes > 1:
                    raise self._fatal(err)
            self._server_requested_wait = plan.delay
        elif isinstance(err, AbyssaleConnectionError):
            # No response to classify — a refused, reset or timed-out request. Treated as transient.
            self._server_requested_wait = None
        else:
            raise self._fatal(err)

        self._transient_failures += 1
        if self._transient_failures > POLL_MAX_TRANSIENT_FAILURES:
            raise self._fatal(err)

    def next_wait(self) -> float:
        """Seconds to sleep before the next poll. Raises when that would cross the deadline."""
        # Honour `Retry-After` when the last failure carried one, else the backoff schedule. No
        # jitter on the server's own figure — it names a window boundary, not a contended resource.
        wait = self._server_requested_wait if self._server_requested_wait is not None else self._interval + _jitter()
        if time.monotonic() + wait > self._deadline:
            raise AbyssalePollingError(
                f"no result after {round(self._options.timeout)}s — the request may still complete"
            )
        # The backoff advances on its own schedule, so a one-off `Retry-After` does not reset the
        # ramp a long-running generation has already built up.
        self._interval = min(self._interval * 2, self._options.max_interval)
        return wait

    @staticmethod
    def _fatal(err: AbyssaleError) -> AbyssalePollingError:
        if isinstance(err, AbyssaleAPIError):
            failure = AbyssalePollingError(err.message, id=err.id, body=err.body)
        else:
            failure = AbyssalePollingError(str(err))
        failure.__cause__ = err
        return failure


def check_generation_result(result: T) -> T:
    """Raise when a finalized generation produced nothing at all.

    **Partial success resolves.** A finalized request can carry both ``banners`` and per-format
    ``errors`` — one format failing does not invalidate the others, so check ``result.errors`` if
    you need every requested format. Only a request that finalized with *no* banners and at least
    one error raises: that is a failed generation, and returning it as a success would leave callers
    iterating an empty ``banners`` list with nothing to indicate why.

    ``id``/``body`` stay reserved for an actual API error body, which this is not — the poll itself
    answered 200. The finalized status object is on ``__cause__.args[0]`` for callers that want to
    read ``errors`` programmatically rather than parse the message.
    """
    banners = getattr(result, "banners", None)
    errors = getattr(result, "errors", None)
    if banners or not errors:
        return result
    reasons = "; ".join(
        f"{getattr(e, 'template_format_name', None) or 'unknown format'}: "
        f"{getattr(e, 'reason', None) or 'no reason given'}"
        for e in errors
    )
    failure = AbyssalePollingError(f"the generation produced no banners — {reasons}")
    failure.__cause__ = AbyssaleError(result)
    raise failure
