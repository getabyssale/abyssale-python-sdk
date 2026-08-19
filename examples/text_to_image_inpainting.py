"""AI image generation (text-to-image) and inpainting.

Set `text_to_image: True` on an image element with `text_to_image_properties` to have Abyssale
generate the image from a prompt instead of using `image_url`. Adding `inpaint_images` switches the
same mode to inpainting — the prompt then describes the edit to apply to those source image(s).

Async only: generate_multi_format_media() accepts it, the synchronous generate_image() answers
400 invalid_payload. It is also ignored on an element that sets `image_url` (other than the
design's default image) or `image_encoded`.

`prompt` needs at least 3 whitespace-separated words. `model`/`ratio`/`quality` are optional and
fall back to the design's own element settings — see which ratio and quality values each model
supports:
https://developers.abyssale.com/rest-api/generation/element-properties/image#text-to-image-inpainting

Run:
    ABYSSALE_API_KEY=your-key python text_to_image_inpainting.py
"""

import sys

from abyssale import Abyssale, AbyssaleAPIError, AbyssalePollingError

DESIGN_ID = "your-design-id"

with Abyssale() as client:
    try:
        # ── Text-to-image: generate a new background from a prompt ────────────
        text_to_image = client.generate_multi_format_media(
            DESIGN_ID,
            {
                "elements": {
                    "background": {
                        "text_to_image": True,
                        "text_to_image_properties": {
                            "prompt": "A sleek, modern glass villa in a minimalist lavender field",
                        },
                    },
                },
            },
        )

        # ── Inpainting: edit an existing image from a prompt ──────────────────
        inpainting = client.generate_multi_format_media(
            DESIGN_ID,
            {
                "elements": {
                    "product_image": {
                        "text_to_image": True,
                        "text_to_image_properties": {
                            "prompt": "enhance the product by adding background decoration",
                            "inpaint_images": ["https://cdn.example.com/product.jpeg"],
                        },
                    },
                    # Shorthand for the same thing — 'prompt,url1[,url2]' is expanded server-side:
                    # "secondary_image": {"text_to_image": "a warm sunset gradient,https://cdn.example.com/o.jpeg"},
                },
            },
        )
    except AbyssaleAPIError as err:
        print(f"Failed to start generation: {err.id} — {err.message}", file=sys.stderr)
        sys.exit(1)

    for label, accepted in (("Text-to-image", text_to_image), ("Inpainting", inpainting)):
        try:
            result = client.wait_for_generation_request(accepted.generation_request_id)
        except AbyssalePollingError as err:
            print(f"{label} polling failed: {err}", file=sys.stderr)
            continue
        print(f"\n{label}:")
        for banner in result.banners:
            print(f" - {banner.file.cdn_url}")
