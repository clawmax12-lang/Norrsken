"""JSON Schema of :class:`CompositionSpec`, the single source of truth for the Remotion worker.

The renderer validates every incoming spec against this schema and derives its TypeScript
types from it, so a contract change in Python can never silently drift from the template.
"""

import json
from pathlib import Path

from preflight.contracts import CompositionSpec

# <repo>/backend/src/preflight/generation/spec_schema.py -> <repo>
_REPO_ROOT = Path(__file__).resolve().parents[4]
SCHEMA_PATH = _REPO_ROOT / "workers" / "renderer" / "schema" / "composition-spec.schema.json"


def composition_schema_json() -> str:
    """Return the canonical, stable text of the schema (sorted keys, trailing newline)."""
    schema = CompositionSpec.model_json_schema(mode="validation")
    return json.dumps(schema, indent=2, sort_keys=True) + "\n"
