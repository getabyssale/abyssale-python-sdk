"""The exception hierarchy.

Unlike the Node SDK — which returns ``{data, error, response}`` and never throws on an HTTP error —
the Python client **raises**. Returning a result object would be unidiomatic here and would make
every call site a two-line unpacking. The *classification* of what went wrong is identical in both
SDKs; only how it is surfaced differs.

Every non-2xx answer from the API carries the same envelope — ``{"id", "message", "errors"?}`` at
every status, on every endpoint — so :attr:`AbyssaleAPIError.id` is populated whenever the response
had a body at all, and callers branch on it rather than on prose.
"""

from __future__ import annotations

from typing import Any


class AbyssaleError(Exception):
    """Base class for everything this SDK raises."""


class AbyssaleConfigError(AbyssaleError):
    """A missing or invalid setting — no API key, a negative timeout, and so on."""


class AbyssaleConnectionError(AbyssaleError):
    """The request never produced a response: DNS, TLS, connection reset, or a timeout.

    The underlying ``httpx`` exception is on ``__cause__``.
    """


class AbyssaleAPIError(AbyssaleError):
    """A non-2xx response.

    Attributes
    ----------
    status:
        The HTTP status code.
    id:
        The API's machine-readable error code (e.g. ``"design_not_found"``). ``None`` only when the
        response had no body or a body that was not the error envelope — which the API does not do,
        but a proxy in front of it might.
    message:
        The human-readable message from the envelope, or a synthesised one.
    errors:
        The per-field problems, when the failure was a payload problem: a flat list of
        ``{"path", "code", "message"}`` (plus optional ``expected``/``received``). ``None`` when the
        failure was not field-scoped — never an empty list.
    body:
        The parsed response body, verbatim.
    response:
        The raw ``httpx.Response``, for headers (rate-limit headers included) and the raw text.
    """

    def __init__(
        self,
        status: int,
        message: str,
        *,
        id: str | None = None,  # noqa: A002 - mirrors the wire field name
        errors: list[dict[str, Any]] | None = None,
        body: Any = None,
        response: Any = None,
    ) -> None:
        super().__init__(f"[abyssale] {status} {id or 'error'}: {message}")
        self.status = status
        self.id = id
        self.message = message
        self.errors = errors
        self.body = body
        self.response = response


class AbyssaleAuthError(AbyssaleAPIError):
    """401 or 403 — unknown key, revoked key, or a plan without API access."""


class AbyssaleNotFoundError(AbyssaleAPIError):
    """404 — the design, format, file or request does not exist in this workspace."""


class AbyssaleRateLimitError(AbyssaleAPIError):
    """429 — three unrelated refusals share this status, distinguished only by :attr:`id`.

    - ``request_rate_limited`` — the per-workspace endpoint budget. Carries ``Retry-After``; wait.
    - ``feature_not_in_plan`` — your plan does not include this design type. Permanent; upgrading
      is the only fix, and the SDK never retries it.
    - ``rate_limit_exceeded`` — **two different things under one id**: either the plan's credits
      are spent (permanent) or the gateway's global 10 req/s ceiling was hit (clears immediately).

    :attr:`retry_after` is the server's own figure in seconds, when it sent one.
    """

    def __init__(self, *args: Any, retry_after: float | None = None, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.retry_after = retry_after


class AbyssalePollingError(AbyssaleError):
    """Raised when a ``wait_for_*`` helper gives up.

    The API's error body is preserved on :attr:`body` (and its machine-readable ``id`` on
    :attr:`id`) rather than being flattened into the message — callers branch on ``id``, never on
    prose. The original failure is always on ``__cause__``.

    Example
    -------
    ::

        try:
            client.wait_for_generation_request(request_id)
        except AbyssalePollingError as err:
            if err.id == "generation_request_not_found":
                ...  # the request has expired
    """

    def __init__(self, detail: str, *, id: str | None = None, body: Any = None) -> None:  # noqa: A002
        super().__init__(f"[abyssale] Polling failed: {detail}")
        self.id = id
        self.body = body


def error_from_response(status: int, body: Any, response: Any, retry_after: float | None = None) -> AbyssaleAPIError:
    """Build the right exception subclass from a non-2xx response.

    The envelope is the single shape the API answers with at every status, so this is the only
    place that reads it.
    """
    envelope = body if isinstance(body, dict) else {}
    error_id = envelope.get("id") if isinstance(envelope.get("id"), str) else None
    message = envelope.get("message") if isinstance(envelope.get("message"), str) else None
    raw_errors = envelope.get("errors")
    # The envelope guarantees `errors` is absent or a non-empty flat array — never a dict, never
    # null, never empty. Anything else came from something that is not the edge.
    errors = raw_errors if isinstance(raw_errors, list) and raw_errors else None

    if not message:
        text = getattr(response, "text", "") or ""
        message = text.strip()[:200] if text.strip() else f"the API answered {status} with no body"

    kwargs: dict[str, Any] = {"id": error_id, "errors": errors, "body": body, "response": response}
    if status == 429:
        return AbyssaleRateLimitError(status, message, retry_after=retry_after, **kwargs)
    if status in (401, 403):
        return AbyssaleAuthError(status, message, **kwargs)
    if status == 404:
        return AbyssaleNotFoundError(status, message, **kwargs)
    return AbyssaleAPIError(status, message, **kwargs)
