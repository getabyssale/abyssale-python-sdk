# Abyssale Python SDK

Official Python client for the [Abyssale API](https://developers.abyssale.com) — generate images,
videos, HTML5 banners and print-ready PDFs from your designs.

**📖 Full reference: [developers.abyssale.com/sdks/python](https://developers.abyssale.com/sdks/python)**
— every method, configuration, error handling, retry behaviour and the polling helpers.

## Install

```bash
pip install abyssale
```

Requires Python 3.10+. This release models API version **`v2026-09-02`** — see
[CHANGELOG.md](https://github.com/getabyssale/abyssale-python-sdk/blob/main/CHANGELOG.md) for the
SDK-to-API version pairing, and `abyssale.__api_version__` to read it at runtime.

## Quick start

```python
from abyssale import Abyssale

with Abyssale() as client:                      # reads ABYSSALE_API_KEY
    design = client.get_design("64238d01-d402-474b-8c2d-fbc957e9d290")

    banner = client.generate_image(design.id, {
        "elements": {"text_title": {"payload": "Summer sale — 40% off"}},
        "template_format_name": "facebook-feed",
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
            "elements": {"text_title": {"payload": "Summer sale — 40% off"}},
            "template_format_names": ["facebook-feed", "instagram-post"],
        })
        result = await client.wait_for_generation_request(accepted.generation_request_id)
        for banner in result.banners:
            print(banner.file.cdn_url)

asyncio.run(main())
```

Methods return the result and **raise** on failure. Branch on the API's machine-readable `id`, never
on the message:

```python
from abyssale import AbyssaleAPIError

try:
    client.generate_image(design_id, {...})
except AbyssaleAPIError as err:
    print(err.status, err.id, err.message, err.errors)
```

## What you get

- **22 methods, sync and async**, one per API operation, named after its `operationId` snake_cased,
  plus two `wait_for_*` polling helpers —
  [every method](https://developers.abyssale.com/sdks/python#every-method)
- **Typed responses, permissive request bodies** — responses are pydantic models that never fail a
  `200`, request bodies pass through untouched —
  [request bodies and responses](https://developers.abyssale.com/sdks/python#request-bodies-and-responses)
- **A typed exception hierarchy** carrying the API's `id`, `errors` and `retry_after` —
  [errors](https://developers.abyssale.com/sdks/python#errors)
- **Narrow retries and a per-attempt timeout**, configurable per client or by environment
  (`ABYSSALE_API_KEY`, `ABYSSALE_TIMEOUT_MS`, `ABYSSALE_MAX_RETRIES`,
  `ABYSSALE_MAX_RETRY_WAIT_MS`) —
  [configuration](https://developers.abyssale.com/sdks/python#configuration) ·
  [what is retried, and what is not](https://developers.abyssale.com/sdks/python#retries-and-timeouts)
- **Webhook signature verification** in `abyssale.webhooks`, which imports only the standard library
  — no client and no API key needed in a receiver process —
  [signature verification](https://developers.abyssale.com/webhooks/signature-verification)

## Examples

Runnable scripts are in [`examples/`](https://github.com/getabyssale/abyssale-python-sdk/blob/main/examples),
including a complete webhook receiver. Each one names its own command:

```bash
ABYSSALE_API_KEY=your-key python examples/generate_image.py
```

## Contributing

See [AGENTS.md](https://github.com/getabyssale/abyssale-python-sdk/blob/main/AGENTS.md) for the
architecture, how to regenerate the models from the OpenAPI spec, and how to add an endpoint.

## Links

- [Abyssale](https://www.abyssale.com) — the product this SDK talks to
- [Documentation](https://developers.abyssale.com/sdks/python)
- [API reference](https://developers.abyssale.com/api-reference/)
- [OpenAPI spec](https://developers.abyssale.com/api.yaml) — the contract this SDK is generated from
- [Source](https://github.com/getabyssale/abyssale-python-sdk)
