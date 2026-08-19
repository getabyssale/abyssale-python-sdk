# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] — 2026-08-19

First release. Covers **every operation in the published OpenAPI spec** — 18 of them — plus two
polling helpers over the spec's status endpoints. Response models are generated from the spec's
schemas.

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
  `feature_not_in_plan` never retried.
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
