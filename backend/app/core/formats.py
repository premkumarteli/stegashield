"""StegaShield Container & Format Specification Module.

Documents protocol constants, headers, and container bitstream layouts.
"""

from __future__ import annotations

from typing import Final

from app.core.crypto import (
    KEY_SIZE_BYTES,
    NONCE_SIZE_BYTES,
    PAYLOAD_TYPE_FILE,
    PAYLOAD_TYPE_TEXT,
    SALT_SIZE_BYTES,
    TAG_SIZE_BYTES,
)
from app.core.stego import (
    HEADER_OVERHEAD_BITS,
    METHOD_LSB_MATCHING,
    METHOD_LSB_REPLACEMENT,
    PROTOCOL_VERSION,
)

CONTAINER_MAGIC: Final[bytes] = b"STGS"

__all__ = [
    "CONTAINER_MAGIC",
    "PROTOCOL_VERSION",
    "HEADER_OVERHEAD_BITS",
    "SALT_SIZE_BYTES",
    "NONCE_SIZE_BYTES",
    "TAG_SIZE_BYTES",
    "KEY_SIZE_BYTES",
    "PAYLOAD_TYPE_TEXT",
    "PAYLOAD_TYPE_FILE",
    "METHOD_LSB_REPLACEMENT",
    "METHOD_LSB_MATCHING",
]
