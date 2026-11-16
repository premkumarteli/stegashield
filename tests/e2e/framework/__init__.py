"""
StegaShield E2E Framework Helpers Package.
"""

from tests.e2e.framework.assertions import (
    assert_lossless_text,
    assert_lossless_file,
    assert_uniform_error,
    assert_capacity_rejection,
    assert_distortion_bounds,
    assert_zero_secrets_leaked,
)
from tests.e2e.framework.reporter import E2EReporter, TestResultItem
from tests.e2e.framework.env_check import run_full_env_check
from tests.e2e.framework.oracles import (
    chi_square_oracle,
    rs_analysis_oracle,
    calibrate_thresholds_oracle,
)

__all__ = [
    "assert_lossless_text",
    "assert_lossless_file",
    "assert_uniform_error",
    "assert_capacity_rejection",
    "assert_distortion_bounds",
    "assert_zero_secrets_leaked",
    "E2EReporter",
    "TestResultItem",
    "run_full_env_check",
    "chi_square_oracle",
    "rs_analysis_oracle",
    "calibrate_thresholds_oracle",
]
