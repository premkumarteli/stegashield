"""StegaShield Core Domain Package.

Pure Python domain logic for cryptography, steganography, and image distortion metrics.
Zero dependencies on web framework or database layers.
"""

from app.core.crypto import (
    WRONG_PASSWORD_OR_NO_DATA,
    StegaShieldError,
    decrypt_payload,
    derive_keys,
    encrypt_payload,
)
from app.core.metrics import (
    calculate_metrics,
    calculate_pov_histogram,
    generate_bitplane,
    generate_diff_heatmap,
)
from app.core.stego import (
    calculate_capacity,
    embed,
    extract,
    validate_cover_image,
)

__all__ = [
    "StegaShieldError",
    "WRONG_PASSWORD_OR_NO_DATA",
    "derive_keys",
    "encrypt_payload",
    "decrypt_payload",
    "calculate_metrics",
    "generate_diff_heatmap",
    "generate_bitplane",
    "calculate_pov_histogram",
    "validate_cover_image",
    "calculate_capacity",
    "embed",
    "extract",
]
