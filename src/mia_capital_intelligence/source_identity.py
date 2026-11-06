"""Verify that local source bytes match an audited inventory entry."""

from hashlib import file_digest
from os import fstat
from pathlib import Path


def verify_pdf(path: Path, *, expected_size: int, expected_sha256: str) -> None:
    """Raise an error for a missing, unrecognized, or altered source."""
    with path.open("rb") as stream:
        if stream.read(5) != b"%PDF-":
            raise ValueError(f"{path}: expected PDF signature")
        if fstat(stream.fileno()).st_size != expected_size:
            raise ValueError(f"{path}: source byte count differs from inventory")
        stream.seek(0)
        if file_digest(stream, "sha256").hexdigest() != expected_sha256:
            raise ValueError(f"{path}: source SHA-256 differs from inventory")
