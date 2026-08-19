#!/usr/bin/env python3
"""Fetch the public OpenAPI spec and strip the Alpha design-import surface.

Port of ``abyssale-nodejs-sdk/scripts/fetch-spec.mjs`` — the exclusion lists below MUST stay
identical to the ones there, or the two SDKs would ship different surfaces from the same spec.

Why this exists: generating straight from the published spec silently pulls in every
``DesignImport*`` path and schema. The exclusion is deliberate — the design-import API is in Alpha
and its contract may change without notice. Doing it here makes the exclusion reproducible instead
of a manual step someone has to remember.

Delete this script (and the ``EXCLUDED_*`` lists) once the design-import API is declared stable.
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any

import yaml

# `ABYSSALE_SPEC_URL` may be an http(s) URL or a local path — the latter is how you regenerate
# against an unpublished spec (e.g. a branch of abyssale-edge-api) before it goes live.
SPEC_URL = os.environ.get("ABYSSALE_SPEC_URL", "https://api-reference.abyssale.com/api.yaml")

#: Paths removed wholesale.
EXCLUDED_PATHS = [
    "/designs/import/json",
    "/designs/import/json/{importId}",
    "/designs/{designId}/as-import",
]

#: Schemas removed wholesale. Prefix-matched, plus the exact names that do not share the prefix.
#: NOTE: `ApiVersion` is deliberately NOT excluded — it is shared with `Design`, `Banner` and
#: `ErrorResponse`, which stay in the SDK.
EXCLUDED_SCHEMA_PREFIXES = ["DesignImport"]
EXCLUDED_SCHEMA_NAMES = ["DesignAsImportResponse"]

_SCHEMA_REF_PREFIX = "#/components/schemas/"


def _is_excluded_schema(name: str) -> bool:
    return name in EXCLUDED_SCHEMA_NAMES or any(name.startswith(p) for p in EXCLUDED_SCHEMA_PREFIXES)


def _read_spec(source: str) -> str:
    if source.startswith(("http://", "https://")):
        import httpx

        response = httpx.get(source, timeout=60.0, follow_redirects=True)
        if response.status_code != 200:
            raise RuntimeError(f"Failed to fetch {source}: {response.status_code} {response.reason_phrase}")
        return response.text
    path = source[len("file://") :] if source.startswith("file://") else source
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def _collect_dangling_refs(node: Any, schemas: dict[str, Any], found: set[str]) -> None:
    if isinstance(node, list):
        for item in node:
            _collect_dangling_refs(item, schemas, found)
        return
    if not isinstance(node, dict):
        return
    for key, value in node.items():
        if key == "$ref" and isinstance(value, str) and value.startswith(_SCHEMA_REF_PREFIX):
            target = value[len(_SCHEMA_REF_PREFIX) :]
            if target not in schemas:
                found.add(target)
        else:
            _collect_dangling_refs(value, schemas, found)


def strip_spec(spec: dict[str, Any]) -> tuple[list[str], list[str], list[str]]:
    """Remove the Alpha surface in place. Returns (paths, schemas, responses) dropped."""
    dropped_paths = []
    paths = spec.get("paths") or {}
    for path in EXCLUDED_PATHS:
        if path in paths:
            del paths[path]
            dropped_paths.append(path)

    components = spec.get("components") or {}
    schemas = components.get("schemas") or {}
    dropped_schemas = [name for name in list(schemas) if _is_excluded_schema(name)]
    for name in dropped_schemas:
        del schemas[name]

    # Shared `components.responses` entries follow the same naming and are referenced only by the
    # excluded paths — but they are not under `paths`, so deleting the paths leaves them behind
    # pointing at schemas that are now gone.
    responses = components.get("responses") or {}
    dropped_responses = [name for name in list(responses) if _is_excluded_schema(name)]
    for name in dropped_responses:
        del responses[name]

    # A dangling $ref would make the generated models reference a schema that no longer exists, so
    # fail loudly rather than emitting something that only breaks at import time.
    dangling: set[str] = set()
    _collect_dangling_refs(spec, schemas, dangling)
    if dangling:
        raise RuntimeError(
            f"Stripping left dangling $refs to: {', '.join(sorted(dangling))}.\n"
            "Either those schemas are still referenced by a kept path, or the exclusion lists in "
            "scripts/fetch_spec.py need updating."
        )
    return dropped_paths, dropped_schemas, dropped_responses


def main(argv: list[str]) -> int:
    out = argv[1] if len(argv) > 1 else "spec.stripped.json"
    spec = yaml.safe_load(_read_spec(SPEC_URL))
    dropped_paths, dropped_schemas, dropped_responses = strip_spec(spec)
    with open(out, "w", encoding="utf-8") as handle:
        json.dump(spec, handle, indent=2)
    print(
        f"Wrote {out} — stripped {len(dropped_paths)} path(s), {len(dropped_schemas)} schema(s) "
        f"and {len(dropped_responses)} shared response(s)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
