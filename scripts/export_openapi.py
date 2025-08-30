"""
Export OpenAPI schema to docs/openapi.json

Usage:
  python -m scripts.export_openapi
"""
from __future__ import annotations

import json
from pathlib import Path

from app.main import app


def main() -> None:
    schema = app.openapi()
    out_path = Path("docs/openapi.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(schema, indent=2))
    print(f"Wrote OpenAPI schema to {out_path}")


if __name__ == "__main__":
    main()

