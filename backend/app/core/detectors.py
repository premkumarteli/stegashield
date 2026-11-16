"""Backward-compatibility alias for app.core.detect.

Re-exports all detector functions, constants, and classifications so external
tools and test adapters importing `app.core.detectors` resolve seamlessly.
"""

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

__all__ = [
    "VERDICT_CLEAN",
    "VERDICT_SUSPICIOUS",
    "VERDICT_LIKELY_STEGO",
    "DEFAULT_THRESHOLDS",
    "chi_square_attack",
    "rs_analysis",
    "classify",
    "classify_verdict",
]
