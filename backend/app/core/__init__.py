"""StegaShield Core Domain Package.

Pure Python domain logic for cryptography, steganography, steganalysis,
image distortion metrics, and attack lab experimentation.
Zero dependencies on web framework or database layers.
"""

from app.core.attack_lab import (
    export_csv,
    run_experiment,
)
from app.core.crypto import (
    WRONG_PASSWORD_OR_NO_DATA,
    StegaShieldError,
    decrypt_payload,
    derive_keys,
    encrypt_payload,
)
from app.core.detect import (
    DEFAULT_THRESHOLDS,
    VERDICT_CLEAN,
    VERDICT_LIKELY_STEGO,
    VERDICT_SUSPICIOUS,
    chi_square_attack,
    classify,
    classify_verdict,
    rs_analysis,
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
    # Cryptography
    "StegaShieldError",
    "WRONG_PASSWORD_OR_NO_DATA",
    "derive_keys",
    "encrypt_payload",
    "decrypt_payload",
    # Steganography
    "validate_cover_image",
    "calculate_capacity",
    "embed",
    "extract",
    # Distortion Metrics
    "calculate_metrics",
    "generate_diff_heatmap",
    "generate_bitplane",
    "calculate_pov_histogram",
    # Steganalysis Detectors
    "chi_square_attack",
    "rs_analysis",
    "classify",
    "classify_verdict",
    "DEFAULT_THRESHOLDS",
    "VERDICT_CLEAN",
    "VERDICT_SUSPICIOUS",
    "VERDICT_LIKELY_STEGO",
    # Attack Lab
    "run_experiment",
    "export_csv",
]
