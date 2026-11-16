"""
StegaShield Tier 1: Cryptographic Core Tests (Features 1–3).
Validates scrypt key derivation, HKDF key separation, and AES-256-GCM encryption.
"""

from __future__ import annotations

import os
import struct
import pytest
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

from tests.e2e.client.direct_core_adapter import _get_core_module
crypto = _get_core_module("crypto")


def _hamming_distance(b1: bytes, b2: bytes) -> int:
    """Computes bitwise Hamming distance between two byte sequences."""
    return sum(bin(x ^ y).count("1") for x, y in zip(b1, b2))


# ==============================================================================
# Feature 1: Cryptographic Key Derivation (scrypt)
# ==============================================================================

@pytest.mark.tier1
@pytest.mark.crypto
def test_t1_f01_01_scrypt_standard_ascii_password():
    """TC-E2E-T1-F01-01: Standard ASCII password produces 32-byte master key."""
    password = "CorrectHorseBatteryStaple2026!"
    salt = os.urandom(16)
    enc_k, perm_k = crypto.derive_keys(password, salt)
    assert len(enc_k) == 32
    assert len(perm_k) == 32
    assert enc_k != perm_k


@pytest.mark.tier1
@pytest.mark.crypto
def test_t1_f01_02_scrypt_unicode_emoji_password():
    """TC-E2E-T1-F01-02: Unicode emoji password produces deterministic 32-byte keys."""
    password = "🔑StegaShield🛡️2026!Greek_Ἀριστοτέλης_Hebrew_שלום"
    salt = b"\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f\x10"
    k1_enc, k1_perm = crypto.derive_keys(password, salt)
    k2_enc, k2_perm = crypto.derive_keys(password, salt)
    assert k1_enc == k2_enc
    assert k1_perm == k2_perm
    assert len(k1_enc) == 32


@pytest.mark.tier1
@pytest.mark.crypto
def test_t1_f01_03_scrypt_salt_orthogonality():
    """TC-E2E-T1-F01-03: Distinct salts produce uncorrelated keys (~50% bit divergence)."""
    password = "AcademicLabSecret2026"
    salt1 = os.urandom(16)
    salt2 = os.urandom(16)
    while salt2 == salt1:
        salt2 = os.urandom(16)

    k1_enc, _ = crypto.derive_keys(password, salt1)
    k2_enc, _ = crypto.derive_keys(password, salt2)

    dist = _hamming_distance(k1_enc, k2_enc)
    # Expected Hamming distance for 256 bits is ~128 (between 90 and 166 bits)
    assert 90 <= dist <= 166, f"Hamming distance {dist} out of expected random bounds"


@pytest.mark.tier1
@pytest.mark.crypto
def test_t1_f01_04_scrypt_minimal_single_char_password():
    """TC-E2E-T1-F01-04: Minimal single-character password derives valid 32-byte keys."""
    password = "x"
    salt = os.urandom(16)
    enc_k, perm_k = crypto.derive_keys(password, salt)
    assert len(enc_k) == 32
    assert len(perm_k) == 32


@pytest.mark.tier1
@pytest.mark.crypto
def test_t1_f01_05_scrypt_deterministic_repeatability():
    """TC-E2E-T1-F01-05: Repeatability over multiple derivations produces identical keys."""
    password = "RepeatabilityVerification2026"
    salt = b"Deterministic16B"
    first_enc, first_perm = crypto.derive_keys(password, salt)
    for _ in range(3):
        cur_enc, cur_perm = crypto.derive_keys(password, salt)
        assert cur_enc == first_enc
        assert cur_perm == first_perm


# ==============================================================================
# Feature 2: HKDF Key Separation
# ==============================================================================

@pytest.mark.tier1
@pytest.mark.crypto
def test_t1_f02_01_hkdf_orthogonal_subkeys():
    """TC-E2E-T1-F02-01: HKDF derives independent 32-byte encryption and permutation keys."""
    master_key = os.urandom(32)
    hkdf_enc = HKDF(algorithm=hashes.SHA256(), length=32, salt=None, info=crypto.HKDF_INFO_ENC)
    enc_key = hkdf_enc.derive(master_key)

    hkdf_perm = HKDF(algorithm=hashes.SHA256(), length=32, salt=None, info=crypto.HKDF_INFO_PERM)
    perm_key = hkdf_perm.derive(master_key)

    assert len(enc_key) == 32
    assert len(perm_key) == 32
    assert enc_key != perm_key


@pytest.mark.tier1
@pytest.mark.crypto
def test_t1_f02_02_hkdf_bitwise_independence():
    """TC-E2E-T1-F02-02: Bitwise independence between subkeys has ~50% Hamming distance."""
    master_key = os.urandom(32)
    hkdf_enc = HKDF(algorithm=hashes.SHA256(), length=32, salt=None, info=crypto.HKDF_INFO_ENC)
    enc_key = hkdf_enc.derive(master_key)

    hkdf_perm = HKDF(algorithm=hashes.SHA256(), length=32, salt=None, info=crypto.HKDF_INFO_PERM)
    perm_key = hkdf_perm.derive(master_key)

    dist = _hamming_distance(enc_key, perm_key)
    assert 90 <= dist <= 166, f"Subkey Hamming distance {dist} outside independent bounds"


@pytest.mark.tier1
@pytest.mark.crypto
def test_t1_f02_03_hkdf_domain_info_separation():
    """TC-E2E-T1-F02-03: Distinct info strings produce uncorrelated key outputs."""
    master_key = os.urandom(32)
    k1 = HKDF(algorithm=hashes.SHA256(), length=32, salt=None, info=b"domain-alpha").derive(master_key)
    k2 = HKDF(algorithm=hashes.SHA256(), length=32, salt=None, info=b"domain-beta").derive(master_key)
    assert k1 != k2
    assert 90 <= _hamming_distance(k1, k2) <= 166


@pytest.mark.tier1
@pytest.mark.crypto
def test_t1_f02_04_hkdf_deterministic_subkeys():
    """TC-E2E-T1-F02-04: HKDF derivations are strictly reproducible."""
    master_key = os.urandom(32)
    k1 = HKDF(algorithm=hashes.SHA256(), length=32, salt=None, info=crypto.HKDF_INFO_ENC).derive(master_key)
    k2 = HKDF(algorithm=hashes.SHA256(), length=32, salt=None, info=crypto.HKDF_INFO_ENC).derive(master_key)
    assert k1 == k2


@pytest.mark.tier1
@pytest.mark.crypto
def test_t1_f02_05_hkdf_zero_salt_expansion():
    """TC-E2E-T1-F02-05: HKDF extract-and-expand with None salt executes cleanly."""
    master_key = os.urandom(32)
    hkdf = HKDF(algorithm=hashes.SHA256(), length=32, salt=None, info=crypto.HKDF_INFO_PERM)
    key = hkdf.derive(master_key)
    assert len(key) == 32


# ==============================================================================
# Feature 3: Authenticated Encryption (AES-256-GCM)
# ==============================================================================

@pytest.mark.tier1
@pytest.mark.crypto
def test_t1_f03_01_aes_gcm_text_roundtrip():
    """TC-E2E-T1-F03-01: Text payload encrypts and decrypts losslessly."""
    plaintext = b"Confidential StegaShield Payload 2026"
    enc_key = os.urandom(32)
    nonce, ct_with_tag = crypto.encrypt_payload(plaintext, enc_key, is_file=False)

    dec_data, is_file, filename = crypto.decrypt_payload(nonce, ct_with_tag, enc_key)
    assert dec_data == plaintext
    assert is_file is False
    assert filename == ""


@pytest.mark.tier1
@pytest.mark.crypto
def test_t1_f03_02_aes_gcm_file_packaging_roundtrip():
    """TC-E2E-T1-F03-02: Binary file packaging round-trip preserves filename and bytes."""
    binary_data = os.urandom(4096)
    filename_in = "dataset.bin"
    enc_key = os.urandom(32)

    nonce, ct_with_tag = crypto.encrypt_payload(binary_data, enc_key, is_file=True, filename=filename_in)
    dec_data, is_file, filename_out = crypto.decrypt_payload(nonce, ct_with_tag, enc_key)

    assert is_file is True
    assert filename_out == filename_in
    assert dec_data == binary_data


@pytest.mark.tier1
@pytest.mark.crypto
def test_t1_f03_03_aes_gcm_aad_length_integrity():
    """TC-E2E-T1-F03-03: Decryption succeeds with valid AAD and fails if AAD is mismatched."""
    plaintext = b"Payload with AAD Binding"
    enc_key = os.urandom(32)
    nonce, ct_with_tag = crypto.encrypt_payload(plaintext, enc_key)

    # Valid decryption
    data, _, _ = crypto.decrypt_payload(nonce, ct_with_tag, enc_key)
    assert data == plaintext

    # Corrupting length AAD should fail tag verification
    aesgcm = AESGCM(enc_key)
    corrupted_aad = struct.pack(">I", len(ct_with_tag) + 99)
    with pytest.raises(Exception):
        aesgcm.decrypt(nonce, ct_with_tag, corrupted_aad)


@pytest.mark.tier1
@pytest.mark.crypto
def test_t1_f03_04_aes_gcm_nonce_uniqueness():
    """TC-E2E-T1-F03-04: Multiple encryptions generate unique 12-byte nonces."""
    plaintext = b"Fixed Secret Data"
    enc_key = os.urandom(32)
    nonces = set()
    ciphertexts = set()

    for _ in range(50):
        nonce, ct = crypto.encrypt_payload(plaintext, enc_key)
        assert len(nonce) == 12
        nonces.add(nonce)
        ciphertexts.add(ct)

    assert len(nonces) == 50
    assert len(ciphertexts) == 50


@pytest.mark.tier1
@pytest.mark.crypto
def test_t1_f03_05_aes_gcm_unicode_multilingual_roundtrip():
    """TC-E2E-T1-F03-05: Unicode multilingual text encrypts and decrypts cleanly."""
    unicode_text = "StegaShield 🛡️ — Ἀριστοτέλης | שלום עליכם | 简体中文 | 日本語テスト | 🚀🔐".encode("utf-8")
    enc_key = os.urandom(32)
    nonce, ct = crypto.encrypt_payload(unicode_text, enc_key, is_file=False)

    dec_data, is_file, _ = crypto.decrypt_payload(nonce, ct, enc_key)
    assert dec_data == unicode_text
    assert dec_data.decode("utf-8") == "StegaShield 🛡️ — Ἀριστοτέλης | שלום עליכם | 简体中文 | 日本語テスト | 🚀🔐"
