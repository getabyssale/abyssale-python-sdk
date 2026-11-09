"""AI asset jobs: generate an image from a prompt, remove its background, then upscale it.

Each action starts a job and answers a ``job_id`` right away; the work runs in the background.
wait_for_asset_job() polls the job until it is COMPLETED (returned) or FAILED (raised). Every action
spends AI credits — check them with get_credits().

For production use, prefer a callback_url: Abyssale then POSTs the ASSET_JOB_FINALIZED webhook once
the job ends, and no process has to wait.

Output URLs are signed and valid 7 days — download the files to keep them.

Run:
    ABYSSALE_API_KEY=your-key python asset_jobs.py
"""

import sys

from abyssale import Abyssale, AbyssaleAPIError, AbyssalePollingError

with Abyssale() as client:
    # Which models can generate an image, and which aspect ratios each one takes.
    listing = client.list_ai_models(operation="images_text_to_image")
    for model in listing.models:
        ratios = model.aspect_ratios.allowed if model.aspect_ratios else []
        print(f"{model.id}{' (default)' if model.is_default else ''}: {ratios}")

    try:
        # 1. Text to image — the workspace's default model, a 16:9 image.
        queued = client.text_to_image(
            {"prompt": "A red sneaker on a white studio background, soft light", "aspect_ratio": "16:9"}
        )
        image = client.wait_for_asset_job(str(queued.job_id))
        image_url = str(image.outputs[0].url)
        print(f"\nGenerated: {image_url} ({image.credits.ai_credits} AI credits)")

        # 2. Remove the background of that image, cropping the transparent edges.
        queued = client.remove_background({"image_url": image_url, "crop": True})
        cut = client.wait_for_asset_job(str(queued.job_id))
        cut_url = str(cut.outputs[0].url)
        print("Background removed:", cut_url)

        # 3. Upscale it 2x.
        queued = client.upscale({"image_url": cut_url, "upscale_factor": 2})
        big = client.wait_for_asset_job(str(queued.job_id))
        print("Upscaled:", big.outputs[0].url)
    except AbyssaleAPIError as err:
        # Refused before anything ran: insufficient_credits, too_many_asset_jobs, unknown_enum_value…
        print(f"Refused: {err.id} — {err.message}", file=sys.stderr)
        sys.exit(1)
    except AbyssalePollingError as err:
        # A FAILED job raises naming its error code (e.g. invalid_input_asset).
        print(f"Job failed: {err}", file=sys.stderr)
        sys.exit(1)
