"""Pack / unpack Qwen3-Embedding vectors for SQLite BLOB storage."""

from __future__ import annotations

import numpy as np

EMBEDDING_DIM = 1024
_EMBEDDING_BYTES = EMBEDDING_DIM * 4  # float32


def pack_embedding(vec: list[float] | np.ndarray) -> bytes:
    """Serialize an L2-normalised embedding to a float32 BLOB."""
    arr = np.asarray(vec, dtype=np.float32).reshape(-1)
    if arr.shape != (EMBEDDING_DIM,):
        raise ValueError(f"embedding must have length {EMBEDDING_DIM}, got {arr.shape[0]}")
    return arr.tobytes()


def unpack_embedding(raw: object) -> np.ndarray | None:
    """Decode a stored embedding BLOB to a float32 vector, or None if invalid."""
    if raw is None:
        return None
    if not isinstance(raw, (bytes, memoryview, bytearray)):
        return None
    data = bytes(raw)
    if len(data) != _EMBEDDING_BYTES:
        return None
    return np.frombuffer(data, dtype=np.float32).copy()
