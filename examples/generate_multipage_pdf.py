"""Multi-page print-ready PDF generation.

generate_multipage_pdf() is for designs of type "printer_multipage". `pages` is a dictionary keyed
by page layer name — each entry can override the root background color for that page.
The result is a single PDF file, ready for commercial printing (crop marks, CMYK color profile).

wait_for_generation_request() handles polling automatically.

Run:
    ABYSSALE_API_KEY=your-key python generate_multipage_pdf.py
"""

import sys

from abyssale import Abyssale, AbyssaleAPIError, AbyssalePollingError

DESIGN_ID = "your-multipage-design-id"

with Abyssale() as client:
    try:
        accepted = client.generate_multipage_pdf(
            DESIGN_ID,
            {
                "pages": {
                    "page_1": {"root": {"background_color": "#FFFFFF"}},
                    "page_2": {"root": {"background_color": "#F5F5F5"}},
                    "page_3": {"root": {"background_color": "#1A1A2E"}},
                },
                "print": {"display_crop_marks": True},
            },
        )
    except AbyssaleAPIError as err:
        print(f"Failed to start PDF generation: {err.id} — {err.message}", file=sys.stderr)
        sys.exit(1)

    print("PDF generation started:", accepted.generation_request_id)

    try:
        result = client.wait_for_generation_request(accepted.generation_request_id)
    except AbyssalePollingError as err:
        print(f"Polling failed: {err}", file=sys.stderr)
        sys.exit(1)

    pdf = result.banners[0]
    print("\nPDF ready:", pdf.file.cdn_url or pdf.file.url)
