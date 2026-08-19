# Abyssale Python SDK

Official Python client for the [Abyssale API](https://developers.abyssale.com) — generate images,
videos, HTML5 banners and print-ready PDFs from your designs.

## Install

```bash
pip install abyssale
```

Requires Python 3.10+.

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

## Configuration

| Variable | Default | Purpose |
|---|---|---|
| `ABYSSALE_API_KEY` | — | Required, unless you pass `api_key=`. |
| `ABYSSALE_TIMEOUT_MS` | `30000` | Per-attempt request timeout. |
| `ABYSSALE_MAX_RETRIES` | `3` | `0` disables retries. |

Every one can be overridden per client: `Abyssale(api_key=..., timeout=60, max_retries=0)`.

## Examples

Runnable scripts are in [`examples/`](examples). Each one names its own command:

```bash
ABYSSALE_API_KEY=your-key python examples/generate_image.py
```

## Contributing

See [AGENTS.md](AGENTS.md) for the architecture, how to regenerate the models from the OpenAPI spec,
and how to add an endpoint.

## Links

- [Documentation](https://developers.abyssale.com/sdks/python)
- [API reference](https://api-reference.abyssale.com)
- [OpenAPI spec](https://api-reference.abyssale.com/api.yaml) — the contract this SDK is generated from
