"""Simple deterministic embedding generator for demo purposes.

In a real deployment this would call a model's embedding endpoint (e.g., via the
provider wrappers). Here we produce a fixed‑length vector by hashing the text and
splitting the hash into float components. The function is pure and suitable for
unit tests.
"""

from __future__ import annotations

import hashlib
from typing import List


def embed_text(text: str, dim: int = 8) -> List[float]:
    """Return a deterministic pseudo‑embedding of ``text``.

    The embedding is derived from the SHA‑256 hash of the input string. The hash
    bytes are interpreted as unsigned integers and normalised to ``[0, 1]``.
    ``dim`` controls the length of the returned vector (must be <= 32).
    """
    if dim <= 0 or dim > 32:
        raise ValueError("dim must be between 1 and 32")
    h = hashlib.sha256(text.encode("utf-8")).digest()
    # Take the first ``dim`` bytes and convert to float in [0,1]
    return [b / 255.0 for b in h[:dim]]
