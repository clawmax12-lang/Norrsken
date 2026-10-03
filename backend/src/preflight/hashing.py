"""Content hashes of files, used to tie results to the exact bytes they describe."""

import hashlib
from pathlib import Path

_CHUNK_BYTES = 1 << 20


def sha256_file(path: Path) -> str:
    """Hex SHA-256 of ``path``, read in chunks (videos are megabytes)."""
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(_CHUNK_BYTES), b""):
            digest.update(chunk)
    return digest.hexdigest()
