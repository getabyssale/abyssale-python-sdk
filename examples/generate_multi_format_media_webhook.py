"""Async multi-format generation with webhook delivery.

Pass a callback_url to generate_multi_format_media() — Abyssale will POST the completed
GenerationRequestStatus payload to that URL when all formats are ready. No polling loop, no open
process required.

This file has two parts:
    1. The generation call that registers the webhook
    2. A minimal HTTP server showing how to receive and type the payload

Run the generation trigger:
    ABYSSALE_API_KEY=your-key python generate_multi_format_media_webhook.py trigger

Run the webhook receiver (must be publicly reachable, e.g. via ngrok):
    python generate_multi_format_media_webhook.py receiver
"""

import json
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer

from abyssale import Abyssale, AbyssaleAPIError, GenerationRequestStatus

DESIGN_ID = "your-design-id"
WEBHOOK_URL = "https://your-server.com/webhooks/abyssale"


# ── Part 1: trigger generation with a callback_url ────────────────────────────


def trigger_generation() -> None:
    with Abyssale() as client:
        try:
            accepted = client.generate_multi_format_media(
                DESIGN_ID,
                {
                    "elements": {
                        "headline": {"payload": "New Product Launch"},
                        "logo": {"image_url": "https://cdn.example.com/logo.png"},
                    },
                    "callback_url": WEBHOOK_URL,
                },
            )
        except AbyssaleAPIError as err:
            print(f"Failed to start generation: {err.id} — {err.message}", file=sys.stderr)
            sys.exit(1)

    print("Generation queued:", accepted.generation_request_id)
    print("Abyssale will POST to", WEBHOOK_URL, "when complete.")


# ── Part 2: webhook receiver ──────────────────────────────────────────────────


class Receiver(BaseHTTPRequestHandler):
    def do_POST(self) -> None:  # noqa: N802 - name fixed by BaseHTTPRequestHandler
        if self.path != "/webhooks/abyssale":
            self.send_response(404)
            self.end_headers()
            return

        length = int(self.headers.get("content-length", 0))
        # Abyssale POSTs the full GenerationRequestStatus when is_finalized is True.
        payload = GenerationRequestStatus.model_validate(json.loads(self.rfile.read(length)))

        print(f"Received {len(payload.banners)} banners:")
        for banner in payload.banners:
            print(f" - {banner.format.id if banner.format else '?'}: {banner.file.cdn_url}")

        self.send_response(200)  # acknowledge — Abyssale retries on non-2xx
        self.end_headers()


def start_receiver() -> None:
    print("Webhook receiver listening on :3000")
    HTTPServer(("", 3000), Receiver).serve_forever()


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else None
    if mode == "trigger":
        trigger_generation()
    elif mode == "receiver":
        start_receiver()
    else:
        print("Usage: python generate_multi_format_media_webhook.py [trigger|receiver]", file=sys.stderr)
        sys.exit(1)
