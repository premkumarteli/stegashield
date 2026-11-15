"""Comprehensive Unit Tests for StegaShield Cryptographic Core.

Covers scrypt KDF, HKDF-SHA256 key separation, AES-256-GCM authenticated
encryption/decryption, AAD length binding, packaging, and uniform error handling.
"""

from __future__ import annotations

import hashlib
import os
import struct
import pytest

from app.core.crypto import (
    KEY_SIZE_BYTES,
    NONCE_SIZE_BYTES,
    SALT_SIZE_BYTES,
    SCRYPT_DKLEN,
    SCRYPT_MAXMEM,
    SCRYPT_N,
    SCRYPT_P,
    SCRYPT_R,
    TAG_SIZE_BYTES,
    WRONG_PASSWORD_OR_NO_DATA,
    StegaShieldError,
    decrypt_payload,
    derive_keys,
    encrypt_payload,
)


def test_scrypt_production_parameters() -> None:
    """Verifies hashlib.scrypt with production parameters succeeds and returns 32 bytes."""
    salt = os.urandom(SALT_SIZE_BYTES)
    key = hashlib.scrypt(
        b"ProductionPasswordTest",
        salt=salt,
        n=SCRYPT_N,
        r=SCRYPT_R,
        p=SCRYPT_P,
        maxmem=SCRYPT_MAXMEM,
        dklen=SCRYPT_DKLEN,
    )
    assert len(key) == 32
    assert isinstance(key, bytes)


def test_scrypt_memory_guard() -> None:
    """Verifies that omitting or setting insufficient maxmem raises ValueError."""
    salt = os.urandom(SALT_SIZE_BYTES)
    with pytest.raises(ValueError, match="memory limit exceeded"):
        hashlib.scrypt(
            b"LowMemoryTest",
            salt=salt,
            n=SCRYPT_N,
            r=SCRYPT_R,
            p=SCRYPT_P,
            maxmem=32 * 1024 * 1024,  # 32 MiB is insufficient for N=131072, r=8
            dklen=SCRYPT_DKLEN,
        )


def test_scrypt_salt_validation() -> None:
    """Asserts derive_keys raises ValueError if salt length is not exactly 16 bytes."""
    with pytest.raises(ValueError, match="Salt must be exactly 16 bytes"):
        derive_keys("valid_password", b"short_salt")
    with pytest.raises(ValueError, match="Salt must be exactly 16 bytes"):
        derive_keys("valid_password", b"0" * 17)
    with pytest.raises(ValueError, match="Salt must be exactly 16 bytes"):
        derive_keys("valid_password", b"")


def test_scrypt_empty_and_unicode_password(fixed_salt: bytes) -> None:
    """Verifies derivation with empty password and Unicode strings."""
    enc_empty, perm_empty = derive_keys("", fixed_salt)
    assert len(enc_empty) == 32 and len(perm_empty) == 32

    enc_uni, perm_uni = derive_keys("pässwørd🔒_secure_🔑", fixed_salt)
    assert len(enc_uni) == 32 and len(perm_uni) == 32
    assert enc_empty != enc_uni


def test_hkdf_orthogonality(derived_test_keys: tuple[bytes, bytes]) -> None:
    """Asserts enc_key != perm_key and each is exactly 32 bytes."""
    enc_key, perm_key = derived_test_keys
    assert len(enc_key) == KEY_SIZE_BYTES
    assert len(perm_key) == KEY_SIZE_BYTES
    assert enc_key != perm_key


def test_hkdf_hamming_distance(derived_test_keys: tuple[bytes, bytes]) -> None:
    """Asserts bitwise Hamming distance between enc_key and perm_key is approximately 50%."""
    enc_key, perm_key = derived_test_keys
    xor_diff = int.from_bytes(enc_key, "big") ^ int.from_bytes(perm_key, "big")
    hamming_dist = bin(xor_diff).count("1")
    # In 256 bits, 50% is 128. Allow natural variance [100, 156]
    assert 100 <= hamming_dist <= 156, f"Hamming distance was {hamming_dist}/256"


def test_hkdf_determinism(test_password: str, fixed_salt: bytes) -> None:
    """Asserts same password + salt produces identical keys."""
    k1_enc, k1_perm = derive_keys(test_password, fixed_salt)
    k2_enc, k2_perm = derive_keys(test_password, fixed_salt)
    assert k1_enc == k2_enc
    assert k1_perm == k2_perm


def test_hkdf_avalanche_effect(test_password: str, fixed_salt: bytes) -> None:
    """Asserts flipping 1 character or byte completely randomizes both keys."""
    base_enc, base_perm = derive_keys(test_password, fixed_salt)
    # Alter 1 byte in password
    mod_pass = test_password[:-1] + ("x" if test_password[-1] != "x" else "y")
    mod_enc, mod_perm = derive_keys(mod_pass, fixed_salt)

    dist_enc = bin(int.from_bytes(base_enc, "big") ^ int.from_bytes(mod_enc, "big")).count("1")
    dist_perm = bin(int.from_bytes(base_perm, "big") ^ int.from_bytes(mod_perm, "big")).count("1")

    assert 100 <= dist_enc <= 156
    assert 100 <= dist_perm <= 156


def test_encrypt_decrypt_text_roundtrip(derived_test_keys: tuple[bytes, bytes]) -> None:
    """Verifies encrypt_payload and decrypt_payload for text."""
    enc_key, _ = derived_test_keys
    text_data = "StegaShield Secret Message 2026! 🔐".encode("utf-8")

    nonce, ct = encrypt_payload(text_data, enc_key, is_file=False)
    assert len(nonce) == NONCE_SIZE_BYTES
    # plaintext length = 1 (type) + 1 (fn_len=0) + len(text_data)
    # ct length = plaintext length + 16 (tag)
    assert len(ct) == 2 + len(text_data) + TAG_SIZE_BYTES

    dec_data, is_file, fn = decrypt_payload(nonce, ct, enc_key)
    assert dec_data == text_data
    assert is_file is False
    assert fn == ""


def test_encrypt_decrypt_file_roundtrip(derived_test_keys: tuple[bytes, bytes]) -> None:
    """Verifies encrypt_payload and decrypt_payload with is_file=True and filename."""
    enc_key, _ = derived_test_keys
    file_bytes = b"\x00\x01\x02\xFF\xFE\xFD" * 100
    fname = "confidential_spec.pdf"

    nonce, ct = encrypt_payload(file_bytes, enc_key, is_file=True, filename=fname)
    dec_data, is_file, fn = decrypt_payload(nonce, ct, enc_key)

    assert dec_data == file_bytes
    assert is_file is True
    assert fn == fname


def test_encrypt_empty_payload_allowed(derived_test_keys: tuple[bytes, bytes]) -> None:
    """Verifies encrypting 0-byte payload produces valid 18-byte ciphertext and decrypts to b''."""
    enc_key, _ = derived_test_keys

    # Empty text
    nonce, ct = encrypt_payload(b"", enc_key, is_file=False)
    assert len(ct) == 1 + 1 + 0 + TAG_SIZE_BYTES  # 18 bytes
    dec_data, is_file, fn = decrypt_payload(nonce, ct, enc_key)
    assert dec_data == b""
    assert is_file is False
    assert fn == ""

    # Empty file
    nonce_f, ct_f = encrypt_payload(b"", enc_key, is_file=True, filename="empty.bin")
    dec_data_f, is_file_f, fn_f = decrypt_payload(nonce_f, ct_f, enc_key)
    assert dec_data_f == b""
    assert is_file_f is True
    assert fn_f == "empty.bin"


def test_encrypt_filename_length_boundary(derived_test_keys: tuple[bytes, bytes]) -> None:
    """Tests 255-byte filename succeeds; 256-byte filename raises ValueError."""
    enc_key, _ = derived_test_keys

    fn_255 = "a" * 255
    nonce, ct = encrypt_payload(b"data", enc_key, is_file=True, filename=fn_255)
    dec_data, is_file, fn = decrypt_payload(nonce, ct, enc_key)
    assert fn == fn_255

    fn_256 = "a" * 256
    with pytest.raises(ValueError, match="Filename exceeds maximum of 255 UTF-8 bytes"):
        encrypt_payload(b"data", enc_key, is_file=True, filename=fn_256)


def test_encrypt_nonce_uniqueness(derived_test_keys: tuple[bytes, bytes]) -> None:
    """Asserts 100 consecutive encryptions of identical data generate 100 unique nonces."""
    enc_key, _ = derived_test_keys
    nonces = set()
    for _ in range(100):
        nonce, _ = encrypt_payload(b"constant", enc_key)
        assert nonce not in nonces
        nonces.add(nonce)
    assert len(nonces) == 100


def test_decrypt_wrong_key_uniform_error(derived_test_keys: tuple[bytes, bytes]) -> None:
    """Asserts decrypting with mismatched key raises StegaShieldError(WRONG_PASSWORD_OR_NO_DATA)."""
    enc_key, _ = derived_test_keys
    nonce, ct = encrypt_payload(b"Secret payload", enc_key)

    wrong_key = os.urandom(32)
    with pytest.raises(StegaShieldError) as exc_info:
        decrypt_payload(nonce, ct, wrong_key)
    assert str(exc_info.value) == WRONG_PASSWORD_OR_NO_DATA


def test_decrypt_wrong_nonce_uniform_error(derived_test_keys: tuple[bytes, bytes]) -> None:
    """Asserts corrupting nonce bytes raises StegaShieldError(WRONG_PASSWORD_OR_NO_DATA)."""
    enc_key, _ = derived_test_keys
    nonce, ct = encrypt_payload(b"Secret payload", enc_key)

    corrupted_nonce = bytearray(nonce)
    corrupted_nonce[0] ^= 0x01
    with pytest.raises(StegaShieldError) as exc_info:
        decrypt_payload(bytes(corrupted_nonce), ct, enc_key)
    assert str(exc_info.value) == WRONG_PASSWORD_OR_NO_DATA


def test_decrypt_corrupted_ciphertext_uniform_error(derived_test_keys: tuple[bytes, bytes]) -> None:
    """Asserts flipping 1 bit in ciphertext raises StegaShieldError(WRONG_PASSWORD_OR_NO_DATA)."""
    enc_key, _ = derived_test_keys
    nonce, ct = encrypt_payload(b"Secret payload", enc_key)

    corrupted_ct = bytearray(ct)
    corrupted_ct[0] ^= 0x01
    with pytest.raises(StegaShieldError) as exc_info:
        decrypt_payload(nonce, bytes(corrupted_ct), enc_key)
    assert str(exc_info.value) == WRONG_PASSWORD_OR_NO_DATA


def test_decrypt_corrupted_tag_uniform_error(derived_test_keys: tuple[bytes, bytes]) -> None:
    """Asserts flipping 1 bit in 16-byte tag raises StegaShieldError(WRONG_PASSWORD_OR_NO_DATA)."""
    enc_key, _ = derived_test_keys
    nonce, ct = encrypt_payload(b"Secret payload", enc_key)

    corrupted_ct = bytearray(ct)
    corrupted_ct[-1] ^= 0x01  # Tag is in last 16 bytes
    with pytest.raises(StegaShieldError) as exc_info:
        decrypt_payload(nonce, bytes(corrupted_ct), enc_key)
    assert str(exc_info.value) == WRONG_PASSWORD_OR_NO_DATA


def test_decrypt_truncated_ciphertext_uniform_error(derived_test_keys: tuple[bytes, bytes]) -> None:
    """Asserts ciphertext < 16 bytes raises StegaShieldError(WRONG_PASSWORD_OR_NO_DATA)."""
    enc_key, _ = derived_test_keys
    with pytest.raises(StegaShieldError) as exc_info:
        decrypt_payload(os.urandom(12), b"short", enc_key)
    assert str(exc_info.value) == WRONG_PASSWORD_OR_NO_DATA


def test_decrypt_corrupted_aad_length(derived_test_keys: tuple[bytes, bytes]) -> None:
    """Asserts invalid length parameters cause tag verification failure."""
    enc_key, _ = derived_test_keys
    nonce, ct = encrypt_payload(b"Payload with bound AAD length", enc_key)

    # If ciphertext is truncated by 1 byte, ct_len calculation will compute different AAD
    with pytest.raises(StegaShieldError) as exc_info:
        decrypt_payload(nonce, ct[:-1], enc_key)
    assert str(exc_info.value) == WRONG_PASSWORD_OR_NO_DATA


def test_error_oracle_resistance(derived_test_keys: tuple[bytes, bytes]) -> None:
    """Validates exc.__cause__ is None and str(exc) == WRONG_PASSWORD_OR_NO_DATA across diverse failure modes."""
    enc_key, _ = derived_test_keys
    nonce, ct = encrypt_payload(b"Test message", enc_key)

    # 1. Invalid tag
    try:
        decrypt_payload(nonce, ct[:-1] + b"\x00", enc_key)
    except StegaShieldError as exc:
        assert exc.__cause__ is None
        assert str(exc) == WRONG_PASSWORD_OR_NO_DATA

    # 2. Invalid key size
    try:
        decrypt_payload(nonce, ct, b"invalid_32_bytes_key")
    except StegaShieldError as exc:
        assert exc.__cause__ is None
        assert str(exc) == WRONG_PASSWORD_OR_NO_DATA

    # 3. Invalid nonce size
    try:
        decrypt_payload(b"short", ct, enc_key)
    except StegaShieldError as exc:
        assert exc.__cause__ is None
        assert str(exc) == WRONG_PASSWORD_OR_NO_DATA

    # 4. Check encrypt_payload invalid enc_key size raises ValueError
    with pytest.raises(ValueError, match="Encryption key must be exactly 32 bytes"):
        encrypt_payload(b"data", b"short_key")

    # 5. Synthetic plaintexts: len < 2
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    aesgcm = AESGCM(enc_key)
    pt_short = b"\x01"
    aad = struct.pack(">I", len(pt_short) + TAG_SIZE_BYTES)
    ct_synth = aesgcm.encrypt(nonce, pt_short, aad)
    with pytest.raises(StegaShieldError) as exc_info:
        decrypt_payload(nonce, ct_synth, enc_key)
    assert str(exc_info.value) == WRONG_PASSWORD_OR_NO_DATA

    # 6. Synthetic plaintexts: unknown type byte
    pt_bad_type = b"\x99\x00data"
    aad = struct.pack(">I", len(pt_bad_type) + TAG_SIZE_BYTES)
    ct_synth = aesgcm.encrypt(nonce, pt_bad_type, aad)
    with pytest.raises(StegaShieldError) as exc_info:
        decrypt_payload(nonce, ct_synth, enc_key)
    assert str(exc_info.value) == WRONG_PASSWORD_OR_NO_DATA

    # 7. Synthetic plaintexts: fn_len exceeds length
    pt_bad_fn_len = b"\x02\x10short"
    aad = struct.pack(">I", len(pt_bad_fn_len) + TAG_SIZE_BYTES)
    ct_synth = aesgcm.encrypt(nonce, pt_bad_fn_len, aad)
    with pytest.raises(StegaShieldError) as exc_info:
        decrypt_payload(nonce, ct_synth, enc_key)
    assert str(exc_info.value) == WRONG_PASSWORD_OR_NO_DATA

    # 8. Synthetic plaintexts: invalid UTF-8 filename
    pt_bad_utf8 = b"\x02\x02\xFF\xFEpayload"
    aad = struct.pack(">I", len(pt_bad_utf8) + TAG_SIZE_BYTES)
    ct_synth = aesgcm.encrypt(nonce, pt_bad_utf8, aad)
    with pytest.raises(StegaShieldError) as exc_info:
        decrypt_payload(nonce, ct_synth, enc_key)
    assert str(exc_info.value) == WRONG_PASSWORD_OR_NO_DATA
