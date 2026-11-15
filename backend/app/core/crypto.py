"""StegaShield Cryptographic Core Module.

Provides scrypt key derivation, HKDF-SHA256 key separation, AES-256-GCM
authenticated encryption/decryption, and uniform error handling.
"""

from __future__ import annotations

import hashlib
import os
import struct
from typing import Final

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

# --- Constants ---
WRONG_PASSWORD_OR_NO_DATA: Final[str] = "WRONG_PASSWORD_OR_NO_DATA"

SCRYPT_N: Final[int] = 131072  # 2^17
SCRYPT_R: Final[int] = 8
SCRYPT_P: Final[int] = 1
SCRYPT_DKLEN: Final[int] = 32
SCRYPT_MAXMEM: Final[int] = 256 * 1024 * 1024  # 256 MiB

SALT_SIZE_BYTES: Final[int] = 16
NONCE_SIZE_BYTES: Final[int] = 12
TAG_SIZE_BYTES: Final[int] = 16
KEY_SIZE_BYTES: Final[int] = 32

HKDF_INFO_ENC: Final[bytes] = b"stegashield-aes256gcm-encryption"
HKDF_INFO_PERM: Final[bytes] = b"stegashield-prng-permutation"

PAYLOAD_TYPE_TEXT: Final[int] = 0x01
PAYLOAD_TYPE_FILE: Final[int] = 0x02


class StegaShieldError(Exception):
    """Base exception for all StegaShield core cryptographic and steganographic errors."""

    pass


def derive_keys(password: str, salt: bytes) -> tuple[bytes, bytes]:
    """Derives (enc_key, perm_key) using scrypt (N=131072, r=8, p=1) + HKDF-SHA256.

    Args:
        password: Plaintext password string.
        salt: Exactly 16 cryptographically random bytes.

    Returns:
        tuple[bytes, bytes]: (enc_key, perm_key) each of length 32 bytes.

    Raises:
        ValueError: If salt length is not exactly 16 bytes.
    """
    if len(salt) != SALT_SIZE_BYTES:
        raise ValueError(
            f"Salt must be exactly {SALT_SIZE_BYTES} bytes, got {len(salt)}"
        )

    master_key = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=SCRYPT_N,
        r=SCRYPT_R,
        p=SCRYPT_P,
        maxmem=SCRYPT_MAXMEM,
        dklen=SCRYPT_DKLEN,
    )

    hkdf_enc = HKDF(
        algorithm=hashes.SHA256(),
        length=KEY_SIZE_BYTES,
        salt=None,
        info=HKDF_INFO_ENC,
    )
    enc_key = hkdf_enc.derive(master_key)

    hkdf_perm = HKDF(
        algorithm=hashes.SHA256(),
        length=KEY_SIZE_BYTES,
        salt=None,
        info=HKDF_INFO_PERM,
    )
    perm_key = hkdf_perm.derive(master_key)

    return enc_key, perm_key


def encrypt_payload(
    data: bytes,
    enc_key: bytes,
    is_file: bool = False,
    filename: str = "",
) -> tuple[bytes, bytes]:
    """Encrypts payload using AES-256-GCM. Returns (nonce, ciphertext_with_tag).

    Packages payload into format:
        [1-byte type (0x01 text, 0x02 file)]
        + [1-byte filename length N]
        + [N bytes filename UTF-8]
        + [payload data bytes]

    Associated Authenticated Data (AAD):
        4-byte big-endian representation of ciphertext_with_tag length:
        struct.pack('>I', len(ciphertext_with_tag))

    Args:
        data: Raw payload bytes to encrypt.
        enc_key: 32-byte AES-256 encryption key.
        is_file: True if payload represents a file; False for text.
        filename: Optional filename for file payloads (max 255 bytes UTF-8).

    Returns:
        tuple[bytes, bytes]: (nonce, ciphertext_with_tag) where nonce is 12 bytes
        and ciphertext_with_tag has length len(packaged_plaintext) + 16.

    Raises:
        ValueError: If enc_key length is invalid or filename exceeds 255 UTF-8 bytes.
    """
    if len(enc_key) != KEY_SIZE_BYTES:
        raise ValueError(
            f"Encryption key must be exactly {KEY_SIZE_BYTES} bytes, got {len(enc_key)}"
        )

    if is_file:
        fn_bytes = filename.encode("utf-8")
        if len(fn_bytes) > 255:
            raise ValueError(
                f"Filename exceeds maximum of 255 UTF-8 bytes: {len(fn_bytes)}"
            )
        p_type = PAYLOAD_TYPE_FILE
    else:
        fn_bytes = b""
        p_type = PAYLOAD_TYPE_TEXT

    plaintext = bytes([p_type, len(fn_bytes)]) + fn_bytes + data
    ct_len = len(plaintext) + TAG_SIZE_BYTES
    aad = struct.pack(">I", ct_len)

    nonce = os.urandom(NONCE_SIZE_BYTES)
    aesgcm = AESGCM(enc_key)
    ciphertext_with_tag = aesgcm.encrypt(nonce, plaintext, aad)

    return nonce, ciphertext_with_tag


def decrypt_payload(
    nonce: bytes,
    ciphertext_with_tag: bytes,
    enc_key: bytes,
) -> tuple[bytes, bool, str]:
    """Decrypts payload. Returns (data, is_file, filename). Raises StegaShieldError(WRONG_PASSWORD_OR_NO_DATA).

    Args:
        nonce: 12-byte initialization vector.
        ciphertext_with_tag: Ciphertext with 16-byte AES-GCM tag appended.
        enc_key: 32-byte AES-256 key.

    Returns:
        tuple[bytes, bool, str]: (data, is_file, filename)

    Raises:
        StegaShieldError: If tag authentication fails, inputs are truncated/malformed,
                          or header values are corrupted. Uniform error message:
                          "WRONG_PASSWORD_OR_NO_DATA".
    """
    try:
        if (
            len(ciphertext_with_tag) < TAG_SIZE_BYTES
            or len(nonce) != NONCE_SIZE_BYTES
            or len(enc_key) != KEY_SIZE_BYTES
        ):
            raise StegaShieldError(WRONG_PASSWORD_OR_NO_DATA)

        ct_len = len(ciphertext_with_tag)
        aad = struct.pack(">I", ct_len)

        aesgcm = AESGCM(enc_key)
        plaintext = aesgcm.decrypt(nonce, ciphertext_with_tag, aad)

        if len(plaintext) < 2:
            raise StegaShieldError(WRONG_PASSWORD_OR_NO_DATA)

        p_type = plaintext[0]
        fn_len = plaintext[1]

        if p_type not in (PAYLOAD_TYPE_TEXT, PAYLOAD_TYPE_FILE):
            raise StegaShieldError(WRONG_PASSWORD_OR_NO_DATA)

        if len(plaintext) < 2 + fn_len:
            raise StegaShieldError(WRONG_PASSWORD_OR_NO_DATA)

        if fn_len > 0:
            try:
                filename = plaintext[2 : 2 + fn_len].decode("utf-8", errors="strict")
            except UnicodeDecodeError:
                raise StegaShieldError(WRONG_PASSWORD_OR_NO_DATA)
        else:
            filename = ""

        data = plaintext[2 + fn_len :]
        is_file = p_type == PAYLOAD_TYPE_FILE

        return data, is_file, filename

    except StegaShieldError:
        raise
    except Exception:
        raise StegaShieldError(WRONG_PASSWORD_OR_NO_DATA) from None
