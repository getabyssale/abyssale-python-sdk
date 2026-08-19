#!/usr/bin/env python3
"""Regenerate ``src/abyssale/_generated.py`` from the published OpenAPI spec.

    python -m pip install -e '.[codegen]'
    python scripts/generate.py

    # against an unpublished edge branch:
    ABYSSALE_SPEC_URL=file:///path/to/abyssale-edge-api/spec/api.yaml python scripts/generate.py

The Alpha design-import surface is stripped first — see ``scripts/fetch_spec.py``.

The output is COMMITTED. Do not edit it by hand; edit the spec and re-run this.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent))
from fetch_spec import SPEC_URL, _read_spec, strip_spec  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT = REPO_ROOT / "src" / "abyssale" / "_generated.py"

HEADER = '''"""Models generated from the Abyssale OpenAPI spec. DO NOT EDIT.

Regenerate with `python scripts/generate.py`. See AGENTS.md.

Every model allows unknown fields (`extra="allow"`): the API ships ahead of the published spec,
and a response carrying a field this SDK has never heard of must not raise.
"""

'''


def main() -> int:
    spec = yaml.safe_load(_read_spec(SPEC_URL))
    dropped_paths, dropped_schemas, dropped_responses = strip_spec(spec)
    print(
        f"Stripped {len(dropped_paths)} path(s), {len(dropped_schemas)} schema(s), "
        f"{len(dropped_responses)} shared response(s) from {SPEC_URL}"
    )

    with tempfile.TemporaryDirectory() as tmp:
        stripped = Path(tmp) / "spec.stripped.json"
        stripped.write_text(json.dumps(spec, indent=2), encoding="utf-8")
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            [
                sys.executable,
                "-m",
                "datamodel_code_generator",
                "--input",
                str(stripped),
                "--input-file-type",
                "openapi",
                "--output",
                str(OUTPUT),
                "--output-model-type",
                "pydantic_v2.BaseModel",
                "--target-python-version",
                "3.10",
                "--use-annotated",
                "--field-constraints",
                "--use-schema-description",
                "--use-standard-collections",
                "--collapse-root-models",
                # The API ships ahead of the spec; an unknown field must never raise.
                "--allow-extra-fields",
                # NOT --snake-case-field: every field in this API is already snake_case, and the
                # flag would silently rename anything that is not, producing a model whose field
                # names no longer match the wire.
                "--disable-timestamp",
            ],
            check=True,
        )

    body = OUTPUT.read_text(encoding="utf-8")
    # datamodel-code-generator writes its own banner; replace it with ours so the "do not edit"
    # notice and the extra="allow" rationale live at the top of the file.
    lines = body.splitlines(keepends=True)
    while lines and (lines[0].startswith("#") or not lines[0].strip()):
        lines.pop(0)
    OUTPUT.write_text(HEADER + "".join(lines), encoding="utf-8")

    leaked = [name for name in ("DesignImport", "DesignAsImport") if name in OUTPUT.read_text(encoding="utf-8")]
    if leaked:
        raise RuntimeError(f"Alpha design-import symbols leaked into the generated models: {leaked}")

    print(f"Wrote {OUTPUT.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
