"""
StegaShield E2E Fixtures - Procedural In-Memory Asset & Payload Generators.
Zero static fixture bloat: generates deterministic images and payloads on the fly.
"""

from __future__ import annotations

import io
import json
import struct
import numpy as np
from PIL import Image
from typing import Tuple, Optional


class ImageGenerator:
    """Procedural generator for synthetic cover images."""

    @staticmethod
    def flat(width: int = 256, height: int = 256, color: Tuple[int, int, int] = (128, 128, 128)) -> Image.Image:
        """Generates a solid uniform color image."""
        arr = np.zeros((height, width, 3), dtype=np.uint8)
        arr[:, :] = color
        return Image.fromarray(arr, mode="RGB")

    @staticmethod
    def boundary_clamped(width: int = 256, height: int = 256, boundary: str = "black") -> Image.Image:
        """Generates an image with all pixel channels at the boundary (0 for black, 255 for white)."""
        val = 0 if boundary == "black" else 255
        arr = np.full((height, width, 3), val, dtype=np.uint8)
        return Image.fromarray(arr, mode="RGB")

    @staticmethod
    def gradient(width: int = 256, height: int = 256, direction: str = "diagonal") -> Image.Image:
        """Generates smooth color gradients."""
        x = np.linspace(0, 255, width, dtype=np.float32)
        y = np.linspace(0, 255, height, dtype=np.float32)
        xx, yy = np.meshgrid(x, y)

        if direction == "horizontal":
            r = xx
            g = 255 - xx
            b = np.full_like(xx, 128)
        elif direction == "vertical":
            r = yy
            g = np.full_like(yy, 128)
            b = 255 - yy
        else:  # diagonal
            r = (xx + yy) / 2.0
            g = (xx + (255 - yy)) / 2.0
            b = ((255 - xx) + yy) / 2.0

        arr = np.stack([r, g, b], axis=2).astype(np.uint8)
        return Image.fromarray(arr, mode="RGB")

    @staticmethod
    def natural_texture(width: int = 256, height: int = 256, seed: int = 42) -> Image.Image:
        """
        Generates an algorithmic pseudo-natural texture (sinusoids + smooth noise).
        Provides realistic Pairs-of-Values distribution and non-zero RS analysis regularity.
        """
        rng = np.random.default_rng(seed)
        x = np.linspace(0, 4 * np.pi, width)
        y = np.linspace(0, 4 * np.pi, height)
        xx, yy = np.meshgrid(x, y)

        base1 = np.sin(xx) * np.cos(yy)
        base2 = np.sin(2 * xx + yy) * np.cos(xx - 2 * yy)

        noise = rng.normal(0, 0.15, (height, width))
        combined = (base1 * 0.5 + base2 * 0.3 + noise) * 45.0 + 128.0
        combined = np.clip(combined, 0, 255).astype(np.uint8)

        # 3 distinct channels to mimic color photography
        r = combined
        g = np.clip(combined.astype(np.int16) + rng.integers(-15, 15, (height, width)), 0, 255).astype(np.uint8)
        b = np.clip(combined.astype(np.int16) + rng.integers(-25, 25, (height, width)), 0, 255).astype(np.uint8)

        arr = np.stack([r, g, b], axis=2)
        return Image.fromarray(arr, mode="RGB")

    @staticmethod
    def step_wedge(width: int = 256, height: int = 256, num_steps: int = 16) -> Image.Image:
        """Generates stepped grayscale bars for histogram / pair-of-values analysis."""
        step_width = max(1, width // num_steps)
        arr = np.zeros((height, width, 3), dtype=np.uint8)
        for i in range(num_steps):
            x_start = i * step_width
            x_end = width if i == num_steps - 1 else (i + 1) * step_width
            val = int((i / (num_steps - 1)) * 255) if num_steps > 1 else 128
            arr[:, x_start:x_end, :] = val
        return Image.fromarray(arr, mode="RGB")

    @staticmethod
    def checkerboard(width: int = 256, height: int = 256, block_size: int = 8) -> Image.Image:
        """Generates high-contrast checkerboard pattern of 0 and 255."""
        x = np.arange(width) // block_size
        y = np.arange(height) // block_size
        xx, yy = np.meshgrid(x, y)
        pattern = ((xx + yy) % 2) * 255
        arr = np.stack([pattern, pattern, pattern], axis=2).astype(np.uint8)
        return Image.fromarray(arr, mode="RGB")

    @staticmethod
    def to_bytes(img: Image.Image, fmt: str = "PNG", quality: int = 95) -> bytes:
        """Converts PIL Image to bytes in target format."""
        buf = io.BytesIO()
        if fmt.upper() in ("JPEG", "JPG"):
            img.save(buf, format="JPEG", quality=quality)
        elif fmt.upper() == "BMP":
            img.save(buf, format="BMP")
        else:
            img.save(buf, format="PNG")
        return buf.getvalue()


class PayloadGenerator:
    """Procedural generator for test text and file payloads."""

    @staticmethod
    def empty() -> str:
        return ""

    @staticmethod
    def single_byte() -> str:
        return "A"

    @staticmethod
    def utf8_complex() -> str:
        return "StegaShield 🛡️ — Ἀριστοτέλης | שלום עליכם | 简体中文 | 日本語テスト | 🚀🔐"

    @staticmethod
    def structured_json(size_approx: int = 1000) -> str:
        """Generates a structured JSON string."""
        num_items = max(1, size_approx // 80)
        data = {
            "title": "StegaShield Automated Academic Test Payload",
            "protocol_version": "1.0.0",
            "records": [
                {"id": i, "token": f"tok_{i:04d}_{i*17 % 997}", "active": (i % 2 == 0)}
                for i in range(num_items)
            ],
        }
        return json.dumps(data, indent=2)

    @staticmethod
    def random_text(size_bytes: int = 1000, seed: int = 42) -> str:
        """Generates deterministic ASCII text of exact byte length."""
        rng = np.random.default_rng(seed)
        chars = np.array(list("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 _-.,\n"))
        indices = rng.integers(0, len(chars), size_bytes)
        return "".join(chars[indices])

    @staticmethod
    def empty_file(filename: str = "empty.bin") -> Tuple[bytes, str]:
        return b"", filename

    @staticmethod
    def realistic_pdf(size_bytes: int = 2048, filename: str = "report.pdf") -> Tuple[bytes, str]:
        """Generates valid minimal PDF binary file."""
        header = b"%PDF-1.5\n%\xe2\xe3\xcf\xd3\n"
        trailer = b"\nxref\n0 1\n0000000000 65535 f \ntrailer\n<< /Size 1 >>\nstartxref\n9\n%%EOF\n"
        body_len = max(0, size_bytes - len(header) - len(trailer))
        body = b"1 0 obj\n<< /Type /Catalog >>\nendobj\n" + b"A" * max(0, body_len - 38)
        return header + body[:body_len] + trailer, filename

    @staticmethod
    def realistic_zip(size_bytes: int = 2048, filename: str = "archive.zip") -> Tuple[bytes, str]:
        """Generates a valid minimal zip structure."""
        buf = io.BytesIO()
        import zipfile
        with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("test.txt", "StegaShield embedded archive payload.")
        base = buf.getvalue()
        if len(base) < size_bytes:
            padding = b"\x00" * (size_bytes - len(base))
            return base + padding, filename
        return base, filename

    @staticmethod
    def binary_random(size_bytes: int = 1024, filename: str = "random.bin", seed: int = 42) -> Tuple[bytes, str]:
        """Generates high-entropy pseudo-random bytes."""
        rng = np.random.default_rng(seed)
        data = rng.bytes(size_bytes)
        return data, filename

    @staticmethod
    def boundary_10mb(filename: str = "max_size.bin") -> Tuple[bytes, str]:
        """Generates exactly 10 MB payload (boundary)."""
        size = 10 * 1024 * 1024
        # Deterministic repeating pattern to keep generation instant
        chunk = b"STEGASHIELD_10MB_PAYLOAD_TESTING_DATA_BLOCK__!" * 20  # 920 bytes
        repeat_count = size // len(chunk)
        remainder = size % len(chunk)
        data = (chunk * repeat_count) + chunk[:remainder]
        return data, filename

    @staticmethod
    def over_limit_10mb_plus(filename: str = "overflow.bin") -> Tuple[bytes, str]:
        """Generates 10 MB + 1024 bytes (exceeds upload limit)."""
        data, _ = PayloadGenerator.boundary_10mb()
        return data + b"\x00" * 1024, filename


class TamperGenerator:
    """Generates corrupted and tampered steganographic images for security testing."""

    @staticmethod
    def corrupt_salt(stego_bytes: bytes, num_bits: int = 4) -> bytes:
        """Flips bits in the first 128 channel slots (sequential salt prefix)."""
        img = Image.open(io.BytesIO(stego_bytes)).convert("RGB")
        arr = np.array(img, dtype=np.uint8)
        flat = arr.reshape(-1)
        for i in range(min(num_bits, 128)):
            flat[i] ^= 1  # flip LSB
        out = Image.fromarray(arr, mode="RGB")
        return ImageGenerator.to_bytes(out, fmt="PNG")

    @staticmethod
    def corrupt_ciphertext(stego_bytes: bytes, num_bits: int = 8) -> bytes:
        """Flips bits in carrier slots beyond 128 (payload slots).
        Since payload bits are pseudo-randomly permuted across all remaining slots,
        we flip bits across the entire carrier beyond slot 128 to ensure all permuted
        ciphertext/tag bits are corrupted without relying on sparse hits.
        """
        img = Image.open(io.BytesIO(stego_bytes)).convert("RGB")
        arr = np.array(img, dtype=np.uint8)
        flat = arr.reshape(-1)
        flat[128:] ^= 1
        out = Image.fromarray(arr, mode="RGB")
        return ImageGenerator.to_bytes(out, fmt="PNG")

    @staticmethod
    def truncate_image(stego_bytes: bytes, crop_ratio: float = 0.5) -> bytes:
        """Crops image to destroy carrier slot geometry."""
        img = Image.open(io.BytesIO(stego_bytes)).convert("RGB")
        w, h = img.size
        new_h = max(16, int(h * crop_ratio))
        cropped = img.crop((0, 0, w, new_h))
        return ImageGenerator.to_bytes(cropped, fmt="PNG")

    @staticmethod
    def transcode_jpeg(stego_bytes: bytes, quality: int = 80) -> bytes:
        """Transcodes stego PNG to lossy JPEG, destroying LSB bit fidelity."""
        img = Image.open(io.BytesIO(stego_bytes)).convert("RGB")
        jpeg_bytes = ImageGenerator.to_bytes(img, fmt="JPEG", quality=quality)
        # Re-encode as PNG so format is accepted but LSBs are corrupted
        reloaded = Image.open(io.BytesIO(jpeg_bytes)).convert("RGB")
        return ImageGenerator.to_bytes(reloaded, fmt="PNG")
