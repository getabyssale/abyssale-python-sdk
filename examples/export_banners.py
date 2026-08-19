"""Batch export — package a set of banners into a downloadable ZIP archive.

export_banners() queues an async export job and returns an export_id. Supply a callback_url to be
notified when the archive is ready — Abyssale will POST to that URL with a download link once the
ZIP is built.

Typical use: after bulk-generating ad creatives, export them all as a ZIP to hand off to a media
buyer or upload to an ad platform.

Run:
    ABYSSALE_API_KEY=your-key python export_banners.py
"""

import sys

from abyssale import Abyssale, AbyssaleAPIError

# IDs of previously generated banners to package
BANNER_IDS = [
    "banner-id-1",
    "banner-id-2",
    "banner-id-3",
]

with Abyssale() as client:
    try:
        export = client.export_banners(
            {
                "ids": BANNER_IDS,
                # Abyssale will POST to this URL with the ZIP download link when ready.
                "callback_url": "https://your-server.com/webhooks/export-ready",
            }
        )
    except AbyssaleAPIError as err:
        print(f"Export failed: {err.id} — {err.message}", file=sys.stderr)
        sys.exit(1)

    print("Export queued.")
    print("Export ID:", export.export_id)
