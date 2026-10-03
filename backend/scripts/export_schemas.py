"""Write the JSON Schema consumed by the Remotion worker (``workers/renderer``).

Run ``uv run python scripts/export_schemas.py`` after any change to ``CompositionSpec``, then
``npm run gen:types`` in ``workers/renderer``. A test fails while the committed file is stale.
"""

from preflight.generation.spec_schema import SCHEMA_PATH, composition_schema_json


def main() -> None:
    """Regenerate the committed schema file."""
    SCHEMA_PATH.parent.mkdir(parents=True, exist_ok=True)
    SCHEMA_PATH.write_text(composition_schema_json(), encoding="utf-8")
    print(f"wrote {SCHEMA_PATH}")  # noqa: T201 - CLI output, not application logging


if __name__ == "__main__":
    main()
