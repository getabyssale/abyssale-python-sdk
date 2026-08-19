"""Dynamic image URL for personalised emails.

create_dynamic_image_url() activates dynamic rendering for a design and returns a per-format base
URL. Append query parameters at send time — the image is rendered on the fly when the recipient
opens the email. No pre-generation, no storage costs, infinite personalised variations.

Run:
    ABYSSALE_API_KEY=your-key python create_dynamic_image_url.py
"""

import sys
from urllib.parse import urlencode

from abyssale import Abyssale, AbyssaleAPIError

DESIGN_ID = "your-design-id"

with Abyssale() as client:
    try:
        dynamic = client.create_dynamic_image_url(DESIGN_ID, {"enable_production_mode": True})
    except AbyssaleAPIError as err:
        print(f"Failed to create dynamic URL: {err.id} — {err.message}", file=sys.stderr)
        sys.exit(1)

    # Each format has its own dynamic_image_url base — append element values as query params.
    params = urlencode(
        {
            "first_name": "Alice",
            "company_name": "Acme Corp",
            "offer_text": "30% off today",
        }
    )
    for image_format in dynamic.formats:
        print(f"{image_format.id}: {image_format.dynamic_image_url}?{params}")
