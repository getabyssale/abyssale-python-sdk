# Contributing to the Abyssale Python SDK

**The [OpenAPI spec](https://api-reference.abyssale.com/api.yaml) is the source of truth for this
SDK.** Everything traces back to it: there is one method per operation, named after that operation's
`operationId` snake_cased (`listDesigns` → `list_designs`); response models are generated from the
spec's schemas; and the retry rules follow the error contract the spec documents. If the SDK and the
spec disagree, the spec is right and the SDK is the bug — unless the *API* disagrees with the spec,
in which case fix the spec (see "Parsing never fails a 200" below).

`tests/test_async_parity.py` pins the method set against the spec's `operationId` list, so an
operation cannot be added to the API and quietly missed here.

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e '.[dev]'
pytest
```

## Architecture

| File | Role |
|---|---|
| `src/abyssale/_client.py` | `Abyssale` — the sync client. The 18 endpoint methods and the 2 `wait_for_*` helpers, each a one-liner over `_request`. This is the file to read first. |
| `src/abyssale/_async_client.py` | `AsyncAbyssale` — a hand-written mirror of the above. |
| `src/abyssale/_retry.py` | Retry classification, derived from the error contract in the spec. Transport-free. |
| `src/abyssale/_polling.py` | `PollLoop` — the poll schedule, the transient-failure budget and the deadline. Transport-free. |
| `src/abyssale/_transport.py` | Request construction and response parsing. Pure. |
| `src/abyssale/_errors.py` | The exception hierarchy and the envelope → exception mapping. |
| `src/abyssale/_config.py` | Argument → env var → default resolution. |
| `src/abyssale/models.py` | The public model surface: re-exports of the generated schemas, plus the hand-written response models. |
| `src/abyssale/_generated.py` | **Generated. Do not edit.** Pydantic models from the OpenAPI spec. |
| `scripts/fetch_spec.py` | Fetches the published spec and strips the Alpha design-import surface. |
| `scripts/generate.py` | The whole regeneration pipeline. |

**Why the async client is a copy and not an abstraction.** Everything that could actually diverge —
retry rules, poll schedule, parsing, config — is in the transport-free modules that both clients
call. What is duplicated is a set of one-line delegations. `tests/test_async_parity.py` compares the
two surfaces by reflection (method names, signatures, defaults, docstrings), so the mirror cannot
silently rot, and eighty trivial lines beat the machinery it would take to generate them.

## Key decisions

**Errors raise.** The spec documents one error envelope — `{id, message, errors?}` — at every
status on every endpoint, so `_errors.py` reads exactly that and raises a typed exception carrying
`id`. Callers branch on `id`, never on `message`, which the spec explicitly describes as unstable.

**Retry rules follow the spec's error contract — read `plan_retry` before changing them.** The
short version: a 5xx is only retried on GET/HEAD/OPTIONS because every POST bills credits; a 429
with `Retry-After` gets the full ladder; a bare 429 gets exactly one one-second probe, because the
spec gives `rate_limit_exceeded` two meanings — "out of credits" (permanent) and the gateway's
10 req/s ceiling (clears instantly) — and nothing in the response distinguishes them;
`feature_not_in_plan` is never retried.

**Request bodies are plain dicts. Responses are models.** The spec's `elements` schema is an `anyOf`
of ten deliberately overlapping branches with *no* discriminator — an element payload carries no
type field, because the layer's type comes from the design. Nothing can validate that offline, and a
model would only mis-coerce it. The API also accepts unknown element and property names by design
(a typo renders the design's saved content, silently), so the SDK must pass bodies through untouched.

**Parsing never fails a 200.** Unknown fields are kept (`extra="allow"`); a field the spec calls
required but the response omits falls back to `model_construct`, which builds the object without
validating. The spec is hand-maintained and the API is the authority. Raising there would turn a
documentation lag into an outage.

**The design-import surface is stripped from the generated models.** The spec marks it Alpha and its
contract may change without notice, so `scripts/fetch_spec.py` removes those paths and schemas before
generation. Delete that carve-out once the spec drops the Alpha marking.

## Regenerating the models

```bash
pip install -e '.[codegen]'
python scripts/generate.py

# against an unpublished edge branch, before the spec is live:
ABYSSALE_SPEC_URL=file:///path/to/abyssale-edge-api/spec/api.yaml python scripts/generate.py
```

`src/abyssale/_generated.py` is committed. The default source is the published bundled spec at
`https://api-reference.abyssale.com/api.yaml` — use that, not the repo's `spec/api.yaml`, whose
local `$ref`s are unresolved.

Only the spec's **named component schemas** are generated. The handful of endpoints whose 2xx body
is an inline `allOf` get hand-written models in `models.py` instead, because code generation names
those after the request path (`DesignsDesignIdFormatsFormatSpecifierGetResponse`) — unreadable, and
unstable across spec edits. If you add a field to one of those responses in the spec, add it to
`models.py` too; until you do it is readable but untyped.

## Adding an endpoint

1. Confirm the operation is in the published spec, and regenerate if it brought new schemas. The
   method name is its `operationId`, snake_cased — do not invent a nicer one.
2. Add the method to `_client.py`, with a docstring and an `Example` block — the docstring is the
   IDE-visible reference and is not optional.
3. Mirror it in `_async_client.py`.
4. Add the `operationId` to the pinned list in `tests/test_async_parity.py`, and a request-shape
   test in `tests/test_client.py`.
5. Add it to `llms.txt`, and to the docs page (`abyssale-developers-doc/docs/sdks/python.md`).

## Testing

`pytest` + `respx` (httpx-native mocking). Two conventions worth knowing:

- The autouse `clock` fixture in `tests/conftest.py` stubs every sleep and drives a virtual clock
  from it. The real schedule still runs — every delay is computed by the real code — but a
  30-minute poll deadline is exercised in milliseconds. Do not use `time.sleep` in a test.
- Tests take the `respx_mock` fixture rather than the `@respx.mock` decorator; as a *class*
  decorator it silently makes the tests uncollectable.

## Release

```bash
make check          # generate + lint + typecheck + test
python -m build
twine upload dist/*
```

Bump the version in **both** `pyproject.toml` and `src/abyssale/_version.py` — the second one is the
User-Agent, and a release that bumps only one ships a User-Agent that lies. Update `CHANGELOG.md`,
then tag `vX.Y.Z`. Manual semver, no CI publish.

The SDK version is its own — it does not track the API's `vYYYY-MM-DD` version. Regenerating against
a new spec release is a normal change like any other; whether it is a minor or a major depends on
what the spec changed.
