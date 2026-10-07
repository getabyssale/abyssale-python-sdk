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
| 1.5.0 | `v2026-10-07` | [spec](https://developers.abyssale.com/api.yaml) |
| 1.4.0 | `v2026-10-01` | |
| 1.3.1 | `v2026-09-25` | |
| 1.3.0 | `v2026-09-24` | |
| 1.2.0 | `v2026-09-02` | |
| 1.1.0 | `v2026-08-21` | |
| 1.0.0 | `v2026-08-20` | |

## [1.5.0] — 2026-10-07

_Generated from API version **`v2026-10-07`**, which also brings `v2026-10-02`._

Minor: the three listings gained keyword arguments. Every existing call keeps working, including
`list_designs(type="static")`: `type` now also takes a list.

### Added

- **Search, filters, sort and paging on `list_designs`** (`v2026-10-07`): `query` (words in any
  order, in the design or the project name), `name`, `project`, `orientation`, `size`, `format`,
  `updated_since`, `created_since`, `sort`, `order`, `page` and `per_page`. `type`, `size` and
  `format` take a string or a list, sent comma-separated as the API expects; the dates take an
  ISO 8601 string, a `date` or a `datetime`.
- **Filters and paging on `list_fonts`** (`name`, `category`, `weight`, `style`) **and
  `list_projects`** (`name`). Both took no argument before.
- **Models**: `Font.category` (Google fonts), and `leonardo-remove-bg` among the background-removal
  models (`v2026-10-02`).

The total across pages (the `X-Total-Count` header) is not exposed: the listings still return a
plain list. When paging, a page shorter than `per_page` is the last one.

## [1.4.0] — 2026-10-01

_Generated from API version **`v2026-10-01`**, which also brings `v2026-09-30`._

Minor: the models gained the upscale settings and new model names. Nothing was removed or narrowed,
so there is no upgrade step beyond installing it.

### Added

- **Upscale on the image element** (`v2026-09-30`): `upscale` and `upscale_properties` on the
  asynchronous image element, modelled by `UpscaleProperties` (`model`: `seedvr-upscale`,
  `topaz-precision`, `crystal-upscaler` or `bria-increase-resolution`; `upscale_factor`: `1` to
  `4`). Asynchronous generation only: the API refuses it on synchronous generation. Request bodies
  stay plain dicts, so this is documentation for what you send, not a new class to import.
- **Three text-to-image and inpainting models** (`v2026-09-30`): `gpt-image-2.5-sunburst`,
  `gpt-image-2.5-flare` and `seedream-5-pro`.
- **`design_in_open_product`** among the documented error ids.

### Changed

- **Colour fields document radial gradients** (`v2026-10-01`). Every field that takes a linear
  gradient also takes `radial-gradient(cx% cy% r%,<stops>)`: a centre and a radius as percentages
  of the layer's box, then the same 2 to 8 stops. A colour is a `str` either way, so only the field
  descriptions changed. See the
  [API changelog](https://developers.abyssale.com/rest-api/changelog).

## [1.3.1] — 2026-09-25

_Generated from API version **`v2026-09-25`**._

Patch: no model gained or lost a field and no type changed — a colour is a `str` either way. The
regeneration only rewrote the descriptions of the colour fields to the one colour grammar
`v2026-09-25` publishes.

### Changed

- **Colour fields document what you may send.** Hex is `#RRGGBB`, `#RRGGBBAA`, `#RGB` or `#RGBA`;
  CMYK is `cmyk(C,M,Y,K)` or `cmyka(C,M,Y,K,A)`, each component an integer 0–100, optionally
  followed by `%`. A gradient stop is `#RRGGBB`, `#RGB` or `cmyk(C,M,Y,K)` — no alpha, its
  transparency is the stop opacity (`0` to `1`) — at an offset of `0%` to `100%`.

### Worth knowing — an API change, not an SDK one

`v2026-09-25` **refuses with `400 invalid_payload`** colours it used to draw wrong or fail on: a
CMYK component or alpha above `100`, a gradient stop offset above `100%`, a stop opacity above `1`
and a 4-digit hex gradient stop. Request bodies are plain dicts passed through untouched, so this
reaches you whatever SDK version you run, as an `AbyssaleAPIError` whose `id` is
`invalid_payload`. See the [API changelog](https://developers.abyssale.com/rest-api/changelog).

## [1.3.0] — 2026-09-24

_Generated from API version **`v2026-09-24`**._

Minor, not patch: the models gained fields. No method changed, no signature moved, and nothing that
worked against 1.2.0 needs touching — a generation body is a plain dict either way.

### Added

- **A `button` element accepts `icon_url` and `icon_color`.** `icon_url` is a public HTTP(s) URL of
  an image to place beside the label; `icon_color` recolours it, and only bites on an **SVG** —
  recolouring rewrites the paint inside the file, and a raster has none to rewrite. Sending
  `icon_url` for a button designed without an icon adds one, rendered on the left at the label's
  font size.

  The icon's geometry — its size, its gap to the label, the side it sits on — belongs to the
  design and is deliberately not overridable per generation, the same way a text layer's font
  family is. Both fields ride the element dict like every other property, so there is nothing new
  to call:

  ```python
  client.generate_image(
      template_id,
      elements={"button_0": {"icon_url": "https://example.com/star.svg", "icon_color": "#FF0000"}},
  )
  ```

- **A `button` element accepts `text_shadow_color`, `text_shadow_blur`, `text_shadow_offset_x` and
  `text_shadow_offset_y`.** A button carries **two** shadows, set separately: the existing
  `shadow_*` properties are the shadow of the button **box**, these four are the shadow of its
  **label**.

- **A `button` element accepts `icon_encoded`.** The base64 / data-URI twin of `icon_url`, for an
  icon held in memory rather than hosted. `icon_url` wins if both are sent, and the icon's geometry
  belongs to the design, not to the generation.

- **An `image` element accepts the five auto-focus properties at the top level**:
  `auto_focus_model`, `focus_objects`, `focus_framing`, `focus_target` and `focus_zoom` — the flat
  form of the matching `auto_focus_properties.*` fields. Both are accepted; the nested one wins
  when both are sent. The `face` model is deprecated in favour of `people` with `focus_framing`.

- **An `image` element accepts `expand` and `expand_properties`.** AI image expansion
  (outpainting): extends the image past its original borders to fill the target area instead of
  cropping or letterboxing it.

### Changed

- **Colour fields document a linear gradient of 2 to 8 stops**, as `v2026-09-24` accepts, instead of
  exactly two, and say where print takes one: only a shape or button `background_color`.
  The models are unchanged — a colour is a `str` either way.

## [1.2.0] — 2026-09-02

_Generated from API version **`v2026-09-02`**._

Minor, not patch: one new client method. Nothing existing changed shape, so there is no upgrade step
beyond installing it.

### Added

- **`get_credits()`** on both clients — the new `GET /credits`, returning the workspace's remaining
  credits for the current billing period as `generation_credits` and `ai_credits`, each a
  `CreditBlock` of `available`, `limit`, `consumed` and `extra`. The read costs no credits.

  Two things to know before branching on the numbers. **`available` and `limit` are `null` on an
  unlimited plan** — and since the generated models type nullable fields as plain `int` (as they do
  for `Design.project_id`), the tolerant parse is what keeps the `None` readable; test for `None`
  before comparing, because `available > 0` raises on an unlimited workspace. And `available` counts
  the **recurring** allowance only, so what a request can still spend is `available + extra`.
- `CreditsBalance` and `CreditBlock` are exported from `abyssale.models`.

## [1.1.0] — 2026-08-21

_Generated from API version **`v2026-08-21`**._

Minor, not patch: three new client methods and a new public module. Nothing existing changed shape,
so there is no upgrade step beyond installing it.

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
