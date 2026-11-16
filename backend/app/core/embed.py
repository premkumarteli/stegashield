"""StegaShield Embed & Extract Module (Canonical Alias).

Re-exports core steganographic embedding and extraction routines.
"""

from __future__ import annotations

from app.core.stego import (
    HEADER_OVERHEAD_BITS,
    METHOD_LSB_MATCHING,
    METHOD_LSB_REPLACEMENT,
    PROTOCOL_VERSION,
    calculate_capacity,
    embed,
    extract,
    validate_cover_image,
)

__all__ = [
    "PROTOCOL_VERSION",
    "HEADER_OVERHEAD_BITS",
    "METHOD_LSB_REPLACEMENT",
    "METHOD_LSB_MATCHING",
    "validate_cover_image",
    "calculate_capacity",
    "embed",
    "extract",
]
