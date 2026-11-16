"""
StegaShield E2E Assertion Helpers.
Standardized domain-specific assertions enforcing cryptographic integrity,
uniform error contracts, visual distortion boundaries, and zero secret leakage.
"""

from __future__ import annotations

from typing import Any, Dict, List, Union
from tests.e2e.client.base import (
    AnalyzeResult,
    DetectResult,
    EmbedResult,
    ExtractResult,
)


def assert_lossless_text(expected: str, result: ExtractResult) -> None:
    """Verifies that an extraction result successfully and losslessly recovered secret text."""
    assert result.success is True, f"Extraction failed with status {result.status_code}: {result.error_detail}"
    assert result.status_code == 200, f"Expected status 200, got {result.status_code}"
    assert result.is_file is False, f"Expected text payload (is_file=False), got is_file={result.is_file}"
    assert result.payload_text == expected, (
        f"Extracted text does not match expected payload.\n"
        f"Expected: {expected[:100]!r}...\n"
        f"Actual:   {str(result.payload_text)[:100]!r}..."
    )


def assert_lossless_file(expected_bytes: bytes, expected_name: str, result: ExtractResult) -> None:
    """Verifies that an extraction result successfully and losslessly recovered a packaged file."""
    assert result.success is True, f"Extraction failed with status {result.status_code}: {result.error_detail}"
    assert result.status_code == 200, f"Expected status 200, got {result.status_code}"
    assert result.is_file is True, f"Expected file payload (is_file=True), got is_file={result.is_file}"
    assert result.filename == expected_name, (
        f"Filename mismatch: expected {expected_name!r}, got {result.filename!r}"
    )
    assert result.payload_bytes is not None, "Payload bytes were None in file extraction"
    assert len(result.payload_bytes) == len(expected_bytes), (
        f"File length mismatch: expected {len(expected_bytes)} bytes, got {len(result.payload_bytes)} bytes"
    )
    assert result.payload_bytes == expected_bytes, "Extracted file content does not match expected bytes"


def assert_uniform_error(result: Union[ExtractResult, EmbedResult, DetectResult]) -> None:
    """
    Verifies that any extraction failure adheres to the strict uniform error contract:
    - Status code must be 400
    - Error detail / code must be exactly 'WRONG_PASSWORD_OR_NO_DATA'
    - Must not leak internal cryptographic failure specifics (tag mismatch, salt corrupted, etc.)
    """
    assert result.success is False, "Expected operation to fail under uniform error contract, but it succeeded"
    assert result.status_code == 400, f"Expected HTTP status 400 for uniform error, got {result.status_code}"

    error_text = f"{result.error_code} {result.error_detail}"
    assert "WRONG_PASSWORD_OR_NO_DATA" in error_text, (
        f"Uniform error contract violated: expected 'WRONG_PASSWORD_OR_NO_DATA', got {error_text!r}"
    )

    # Verify no internal leakage keywords
    forbidden = ["InvalidTag", "TagMismatch", "MacError", "KeyError", "scrypt", "AESGCM", "Traceback"]
    for word in forbidden:
        assert word not in error_text, f"Internal secret/cryptographic reason leaked in error: {word} in {error_text}"


def assert_capacity_rejection(result: EmbedResult) -> None:
    """Verifies that an oversized payload was cleanly rejected prior to allocation."""
    assert result.success is False, "Expected embedding to fail due to capacity limits, but it succeeded"
    assert result.status_code in (400, 413), (
        f"Expected HTTP status 400 or 413 for capacity rejection, got {result.status_code}"
    )
    err = f"{result.error_code} {result.error_detail}".lower()
    assert any(term in err for term in ["capacity", "large", "too big", "payloadexceeds", "overflow", "dimension", "413"]), (
        f"Expected capacity rejection error message, got: {result.error_detail}"
    )


def assert_distortion_bounds(
    metrics: Dict[str, float],
    min_psnr: float = 40.0,
    max_mse: float = 2.0,
    min_ssim: float = 0.95,
) -> None:
    """Verifies that mathematical visual quality remains within acceptable steganographic bounds."""
    assert "mse" in metrics, f"MSE metric missing from {metrics}"
    assert "psnr" in metrics, f"PSNR metric missing from {metrics}"
    assert "ssim" in metrics, f"SSIM metric missing from {metrics}"

    mse = float(metrics["mse"])
    psnr = float(metrics["psnr"])
    ssim = float(metrics["ssim"])

    assert mse <= max_mse, f"MSE {mse} exceeded maximum threshold of {max_mse}"
    assert psnr >= min_psnr, f"PSNR {psnr} dB was below minimum threshold of {min_psnr} dB"
    assert ssim >= min_ssim, f"SSIM {ssim} was below minimum threshold of {min_ssim}"


def assert_zero_secrets_leaked(data: Union[Dict[str, Any], str, List[Any]], forbidden_secrets: List[str]) -> None:
    """Scans structured dictionaries, lists, or text to ensure no passwords, keys, or salts appear."""
    text_repr = str(data)
    for secret in forbidden_secrets:
        if secret and len(secret) > 3:
            assert secret not in text_repr, f"Secret leaked in output: {secret[:4]}*** found in data"
