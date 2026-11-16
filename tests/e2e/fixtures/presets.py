"""
StegaShield E2E Fixtures - Standardized Test Presets.
"""

from __future__ import annotations

from typing import Dict, List, Tuple
from tests.e2e.fixtures.generators import ImageGenerator, PayloadGenerator

# Standard Passwords
PASSWORD_VALID = "CorrectHorseBatteryStaple2026!"
PASSWORD_ACADEMIC = "AcademicLabSecret2026"
PASSWORD_COMPLEX = "P@ssw0rd🛡️2026!KeySeparation"
PASSWORD_WRONG = "TotallyIncorrectPassword123"

# Standard Embedding Methods
METHOD_LSB_REPLACEMENT = "lsb_replacement"
METHOD_LSB_MATCHING = "lsb_matching"
ALL_METHODS = [METHOD_LSB_REPLACEMENT, METHOD_LSB_MATCHING]

# Standard Experiment Ratios & Detectors
EXPERIMENT_RATIOS = [0.05, 0.10, 0.25, 0.50, 1.00]
EXPERIMENT_DETECTORS = ["chi_square", "rs_analysis"]

# Dimensions
DIM_MICRO = (64, 64)
DIM_STANDARD = (256, 256)
DIM_LARGE = (512, 512)
DIM_BOUNDARY_16MP = (4000, 4000)
DIM_OVER_16MP = (4096, 4096)


def get_standard_cover_bytes(fmt: str = "PNG") -> bytes:
    """Returns standard 256x256 natural texture image bytes in requested format."""
    img = ImageGenerator.natural_texture(256, 256, seed=42)
    return ImageGenerator.to_bytes(img, fmt=fmt)


def get_micro_cover_bytes(fmt: str = "PNG") -> bytes:
    """Returns fast 64x64 gradient cover bytes (<1ms execution)."""
    img = ImageGenerator.gradient(64, 64)
    return ImageGenerator.to_bytes(img, fmt=fmt)
