"""Synchronous single-image generation.

generate_image() returns the finished banner immediately — no polling needed.
Use this for one-off renders or low-volume flows where latency is acceptable.

Run:
    ABYSSALE_API_KEY=your-key python generate_image.py
"""

import sys

from abyssale import Abyssale, AbyssaleAPIError

DESIGN_ID = "your-design-id"

with Abyssale() as client:
    try:
        banner = client.generate_image(
            DESIGN_ID,
            {
                "template_format_name": "instagram-square",
                "elements": {
                    "headline": {"payload": "Summer Sale — 50% Off"},
                    "product_image": {"image_url": "https://cdn.example.com/product.jpg"},
                    "cta_button": {"payload": "Shop Now", "background_color": "#FF6B35"},
                },
            },
        )
    except AbyssaleAPIError as err:
        print(f"Generation failed: {err.id} — {err.message}", file=sys.stderr)
        sys.exit(1)

    print("Banner ID  :", banner.id)
    print("CDN URL    :", banner.file.cdn_url)
    print("Format     :", banner.format.id if banner.format else None)
