"""Async multi-format generation with built-in polling.

generate_multi_format_media() starts an async job that renders the same design across every format
simultaneously (images, GIFs, videos, HTML5, PDFs). wait_for_generation_request() polls
automatically with exponential backoff until all formats are ready, then returns the completed
result.

For production use, prefer a callback_url to avoid holding an open process —
see generate_multi_format_media_webhook.py.

Run:
    ABYSSALE_API_KEY=your-key python generate_multi_format_media.py
"""

import sys

from abyssale import Abyssale, AbyssaleAPIError, AbyssalePollingError

DESIGN_ID = "your-design-id"

with Abyssale() as client:
    try:
        accepted = client.generate_multi_format_media(
            DESIGN_ID,
            {
                "elements": {
                    "headline": {"payload": "New Product Launch"},
                    "logo": {"image_url": "https://cdn.example.com/logo.png"},
                    "background": {"background_color": "#1A1A2E"},
                },
            },
        )
    except AbyssaleAPIError as err:
        print(f"Failed to start generation: {err.id} — {err.message}", file=sys.stderr)
        sys.exit(1)

    print("Generation started:", accepted.generation_request_id)

    try:
        # Polls with exponential backoff until is_finalized is True; raises on timeout.
        result = client.wait_for_generation_request(accepted.generation_request_id)
    except AbyssalePollingError as err:
        print(f"Polling failed: {err}", file=sys.stderr)
        sys.exit(1)

    print(f"\nGenerated {len(result.banners)} banners:")
    for banner in result.banners:
        print(f" - {banner.format.id if banner.format else '?'}: {banner.file.cdn_url}")

    # A finalized request can carry both banners and per-format errors — one format failing does
    # not invalidate the others.
    for error in result.errors or []:
        print(f" ! {error.template_format_name}: {error.reason}", file=sys.stderr)
