# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

**Every release names the API version it was generated from.** The API is versioned by release date
(`vYYYY-MM-DD`) and one version is maintained at a time, so the pairing below tells you which
contract a given SDK release models. The SDK's own version is independent — regenerating against a
newer API version is a normal change, and whether it is a patch, minor or major depends on what the
API changed.

| SDK | API version | |
|---|---|---|
| 1.0.0 | `v2026-08-20` | [spec](https://api-reference.abyssale.com/api.yaml) |

## [Unreleased]

_Not published. The API surface this tracks is itself unreleased, so the version in
`pyproject.toml` / `_version.py` is bumped when the release goes out, not when the change lands. The
table above is unchanged for the same reason: these endpoints are not in `v2026-08-20`, and
`__api_version__` will be updated by the release that publishes them._

### Added

- **`abyssale.webhooks`** — a new **public** module (the third, after `abyssale` and
  `abyssale.models`) with `verify_webhook_signature` and `signature_timestamp`. It imports **only
  the standard library**: no client, no `httpx`. That is the point of it being separate — a process
  that only receives deliveries should not have to hold a credential that can spend credits, and a
  test asserts the import graph so the property cannot rot.

  Pass the **raw** body: the signature covers the bytes as sent, so a parsed-and-re-serialised dict
  reorders keys and never matches. It returns `False` and never raises on a missing, malformed,
  forged or stale header — anyone who finds a webhook URL can POST to it, and an exception in a
  handler is a 500 plus, on most frameworks, a retried delivery. It checks **every** `v1` in the
  header, because a rotation puts two there for 24 hours.
- **`get_signing_secret()`, `rotate_signing_secret(force=False)`, `revoke_signing_secret()`** on
  both clients — the three `/signing-secret` endpoints. Deliveries are unsigned until
  `get_signing_secret()` is called once; fetching the secret is what turns signing on. A refused
  second rotate raises `AbyssaleAPIError` with `id="previous_secret_still_active"` and is **not
  retried** — it is a state conflict, not a transient failure. `force` is omitted from the query
  string entirely when false, so an ordinary rotate stays a bare `POST`.
- `SigningSecret` response model, generated from the spec.

## [1.0.0] — 2026-08-20

_Generated from API version **`v2026-08-20`**._

First release. Covers **every operation in that spec** — 18 of them — plus two polling helpers over
its status endpoints. Response models are generated from its schemas.

### Added

- `Abyssale` and `AsyncAbyssale`, over `httpx`. Both are context managers and both accept a
  caller-supplied `httpx` client.
- All 18 endpoints: auth; design list/read/format read; sync and async generation; multipage PDF;
  generation-request status; file read; fonts; projects list/create; export; dynamic image URL;
  workspace templates, categories, duplication and duplication status.
- `wait_for_generation_request` and `wait_for_duplication_request` — exponential backoff with
  jitter, a 30-minute default deadline, and a budget of three *consecutive* transient failures that
  resets on any successful poll. Partial success resolves: a finalized request carrying both banners
  and per-format errors is a result, not an exception. Only a request that finalized with no banners
  at all and at least one error raises.
- Retries, following the spec's error contract: 5xx on idempotent methods only
  (every POST bills credits, and a 504 does not mean the render did not happen); the full ladder for
  a `429` carrying `Retry-After`; exactly one one-second probe for a bare `429`, because
  `rate_limit_exceeded` conflates spent credits with the gateway's per-second ceiling;
  `feature_not_in_plan` never retried, whatever headers the response carries — no window makes a
  plan restriction clear.
- `max_retry_wait` (`$ABYSSALE_MAX_RETRY_WAIT_MS`, default 30s) — the longest single `Retry-After`
  the SDK will sleep through on your behalf. The rate limiter can name a cool-off of ~1700s once a
  quota is spent, and `max_retries` multiplies it, so honouring it blindly would turn one call into
  83 minutes of silence with no way to intervene. Past the bound the call fails immediately with
  `AbyssaleRateLimitError`, `retry_after` carrying the server's figure so the decision is yours.
  Applies to any server-named wait, including a 5xx that carries `Retry-After` and one absorbed by a
  `wait_for_*` poll — a 30-minute deadline has room to sleep off a 28-minute cool-off in one go, and
  the bound is what refuses it. The SDK's own backoff and the bare-`429` probe are unaffected. Pass
  `math.inf` to wait however long the server asks.
- An exception hierarchy under `AbyssaleError`, built from the API's single error envelope — the
  machine-readable `id` is always on the exception, and `errors` holds the per-field problems when
  the failure was a payload problem.
- Pydantic response models generated from the spec, with the Alpha design-import surface stripped by
  `scripts/fetch_spec.py`, since the spec marks that surface Alpha.
- Seven runnable examples in `examples/`, each exercising a documented operation end to end.

### Notes

- **Request bodies are plain dicts.** The `elements` schema is an `anyOf` of ten deliberately
  overlapping branches with no discriminator, and the API accepts unknown element names by design,
  so bodies are passed through untouched rather than modelled.
- **Parsing never fails a successful response.** Unknown fields are kept, and a field the spec calls
  required but the response omits does not raise — the spec is hand-maintained and the API is the
  authority.
- Requires Python 3.10+.
