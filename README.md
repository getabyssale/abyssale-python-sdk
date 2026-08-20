# Abyssale Python SDK

Official Python client for the [Abyssale API](https://developers.abyssale.com) — generate images,
videos, HTML5 banners and print-ready PDFs from your designs.

## Install

```bash
pip install abyssale
```

Requires Python 3.10+. This release models API version **`v2026-08-20`** — see
[CHANGELOG.md](https://github.com/getabyssale/abyssale-python-sdk/blob/main/CHANGELOG.md) for the SDK-to-API version pairing, and `abyssale.__api_version__` to
read it at runtime.

## Quick start

```python
from abyssale import Abyssale

with Abyssale() as client:                      # reads ABYSSALE_API_KEY
    design = client.get_design("64238d01-d402-474b-8c2d-fbc957e9d290")

    banner = client.generate_image(design.id, {
        "elements": {"title": {"payload": "Hello World"}},
        "template_format_name": "facebook-post",
    })
    print(banner.file.cdn_url)
```

Async is the same surface:

```python
import asyncio
from abyssale import AsyncAbyssale

async def main():
    async with AsyncAbyssale() as client:
        accepted = await client.generate_multi_format_media(design_id, {
            "elements": {"title": {"payload": "Summer Sale"}},
            "template_format_names": ["facebook-feed", "instagram-post"],
        })
        result = await client.wait_for_generation_request(accepted.generation_request_id)
        for banner in result.banners:
            print(banner.file.cdn_url)

asyncio.run(main())
```

## Verifying webhook deliveries

Abyssale signs every delivery once the workspace has a signing secret, so a receiver can tell a real
delivery from anything else that finds the URL. Fetch the secret once and store it like a password:

```python
secret = client.get_signing_secret().secret     # mints it on the first call
```

Verify with the raw request body. `abyssale.webhooks` imports only the standard library — no client,
no `httpx` — so a receiver process needs no API key:

```python
from abyssale.webhooks import verify_webhook_signature

@app.post("/webhooks/abyssale")
def receive():
    if not verify_webhook_signature(
        request.get_data(),                      # RAW bytes, exactly as received
        request.headers.get("X-Abyssale-Signature"),
        SIGNING_SECRET,
    ):
        return "", 401
    ...
```

Four things decide whether this works:

- **Pass the raw bytes.** The signature covers what was sent, so a parsed-and-re-serialised dict
  reorders keys and never matches. `request.get_data()` in Flask, `await request.body()` in FastAPI,
  `request.body` in Django — never `json.dumps(request.json)`.
- **It returns `False` and never raises** — on a missing, malformed, forged or stale header alike.
  Anyone who finds your URL can POST to it, and an exception in a handler is a 500.
- **A rotation puts two signatures in the header.** For 24 hours after `rotate_signing_secret()`
  every delivery carries one `v1` per valid secret, so a receiver holding either one verifies and
  you can deploy on your own schedule. Every `v1` is checked.
- **Deduplicate on `X-Abyssale-Delivery-Id`**, 64 lowercase hex characters. It is present whether or
  not the delivery is signed and does not change between attempts — a delivery that exhausts the
  retry ladder arrives six times with the same id, while the signature's `t` is new each time. The
  id identifies a delivery, not an event: one event fanned out to several subscribed URLs gives each
  subscription its own id, which is all deduplication needs but is not a value two of your endpoints
  can correlate on. Use the payload's own ids for that.

Until `get_signing_secret()` is called once, deliveries are **unsigned** — fetching the secret is
what turns signing on. `rotate_signing_secret()` refuses a second rotate inside the 24-hour window
with `AbyssaleAPIError(id="previous_secret_still_active")`, because it would drop the secret your
receiver is still using; `revoke_signing_secret()` ends the overlap deliberately.

`examples/generate_multi_format_media_webhook.py` is a complete receiver doing all of this.

## Errors

Methods return the result and **raise** on failure. Branch on the API's machine-readable `id`, not
on the message:

```python
from abyssale import AbyssaleAPIError, AbyssaleRateLimitError

try:
    client.generate_image(design_id, {...})
except AbyssaleRateLimitError as err:
    if err.id == "feature_not_in_plan":
        ...                                     # your plan excludes this design type
except AbyssaleAPIError as err:
    print(err.status, err.id, err.message, err.errors)
```

`err.errors` holds the per-field problems (`path`, `code`, `message`) when the request body was the
problem, and is `None` otherwise.

Transient failures are retried for you: 5xx on reads, and `429`s that carry a `Retry-After`. A `429`
without one gets a single one-second probe, because the status is shared by "out of credits"
(permanent) and the gateway's per-second ceiling (clears immediately). Writes are never retried on a
5xx — a timed-out generation may still have been billed.

A `Retry-After` is only waited out up to `max_retry_wait` (30s by default). The rate limiter can name
a cool-off of half an hour once a quota is spent, and sleeping through that — times `max_retries` —
turns one call into an hour of silence. Past the bound the call fails immediately instead, with
`err.retry_after` carrying the server's figure so you can decide what to do with it. Pass
`max_retry_wait=math.inf` if you do want to wait however long the server asks.

## Configuration

| Variable | Default | Purpose |
|---|---|---|
| `ABYSSALE_API_KEY` | — | Required, unless you pass `api_key=`. |
| `ABYSSALE_TIMEOUT_MS` | `30000` | Per-attempt request timeout. |
| `ABYSSALE_MAX_RETRIES` | `3` | `0` disables retries. |
| `ABYSSALE_MAX_RETRY_WAIT_MS` | `30000` | Longest `Retry-After` to wait out. `inf` to never give up. |

Every one can be overridden per client: `Abyssale(api_key=..., timeout=60, max_retries=0)`.

## Examples

Runnable scripts are in [`examples/`](https://github.com/getabyssale/abyssale-python-sdk/blob/main/examples). Each one names its own command:

```bash
ABYSSALE_API_KEY=your-key python examples/generate_image.py
```

## Contributing

See [AGENTS.md](https://github.com/getabyssale/abyssale-python-sdk/blob/main/AGENTS.md) for the architecture, how to regenerate the models from the OpenAPI spec,
and how to add an endpoint.

## Links

- [Abyssale](https://www.abyssale.com) — the product this SDK talks to
- [Documentation](https://developers.abyssale.com/sdks/python)
- [API reference](https://api-reference.abyssale.com)
- [OpenAPI spec](https://api-reference.abyssale.com/api.yaml) — the contract this SDK is generated from
- [Source](https://github.com/getabyssale/abyssale-python-sdk)
