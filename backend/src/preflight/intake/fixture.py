"""Load the committed demo brief from ``fixtures/`` (FR-01 fixture)."""

from pathlib import Path

from pydantic import ValidationError

from preflight.contracts import Brief
from preflight.errors import StorageError


def load_fixture_brief(path: Path) -> Brief:
    """Read a ``brief.json`` fixture and validate it against the :class:`Brief` contract.

    The tablehopp fixture holds placeholder screenshots until the product owner supplies
    real ones, so its paths are not files that exist on disk.

    Raises:
        StorageError: The file is missing or does not match the contract.
    """
    try:
        return Brief.model_validate_json(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise StorageError(f"missing file: {path}") from exc
    except ValidationError as exc:
        raise StorageError(f"invalid Brief in {path}: {exc}") from exc
