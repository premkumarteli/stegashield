"""Tests for Steganography API endpoints (embed, extract, analyze, detect)."""

import io
from fastapi.testclient import TestClient
from PIL import Image


def test_embed_and_extract_text_roundtrip(client: TestClient, cover_image_bytes: bytes) -> None:
    password = "CorrectSecretPassword2026!"
    secret_text = "StegaShield authenticated encryption payload test."

    # 1. Embed text
    embed_res = client.post(
        "/api/v1/stego/embed",
        data={
            "password": password,
            "payload_type": "text",
            "payload_text": secret_text,
            "method": "lsb_replacement",
        },
        files={
            "cover_file": ("test_cover.png", cover_image_bytes, "image/png"),
        },
    )
    assert embed_res.status_code == 200
    embed_data = embed_res.json()
    assert "operation_id" in embed_data
    assert "download_url" in embed_data
    assert embed_data["metrics"]["mse"] >= 0.0
    assert embed_data["metrics"]["psnr"] > 0.0
    assert embed_data["metrics"]["ssim"] > 0.0

    # 2. Download stego file
    stego_res = client.get(embed_data["download_url"])
    assert stego_res.status_code == 200
    stego_bytes = stego_res.content

    # 3. Extract text
    extract_res = client.post(
        "/api/v1/stego/extract",
        data={"password": password},
        files={"stego_file": ("stego.png", stego_bytes, "image/png")},
    )
    assert extract_res.status_code == 200
    extract_data = extract_res.json()
    assert extract_data["payload_type"] == "text"
    assert extract_data["payload_text"] == secret_text


def test_embed_and_extract_file_roundtrip(client: TestClient, cover_image_bytes: bytes) -> None:
    password = "FileSecretPassword2026!"
    raw_bin_payload = b"\x00\x01\x02\x03\x04\x05\xff\xfe\xfd\xfc" * 20

    # 1. Embed file
    embed_res = client.post(
        "/api/v1/stego/embed",
        data={
            "password": password,
            "payload_type": "file",
            "method": "lsb_matching",
        },
        files={
            "cover_file": ("test_cover.png", cover_image_bytes, "image/png"),
            "payload_file": ("secret.bin", raw_bin_payload, "application/octet-stream"),
        },
    )
    assert embed_res.status_code == 200
    embed_data = embed_res.json()

    # 2. Download stego
    stego_res = client.get(embed_data["download_url"])
    assert stego_res.status_code == 200
    stego_bytes = stego_res.content

    # 3. Extract file
    extract_res = client.post(
        "/api/v1/stego/extract",
        data={"password": password},
        files={"stego_file": ("stego.png", stego_bytes, "image/png")},
    )
    assert extract_res.status_code == 200
    extract_data = extract_res.json()
    assert extract_data["payload_type"] == "file"
    assert extract_data["filename"] == "secret.bin"
    assert "download_url" in extract_data

    # 4. Download extracted file payload
    file_dl = client.get(extract_data["download_url"])
    assert file_dl.status_code == 200
    assert file_dl.content == raw_bin_payload


def test_extract_wrong_password_uniform_error(client: TestClient, cover_image_bytes: bytes) -> None:
    # Embed with correct password
    embed_res = client.post(
        "/api/v1/stego/embed",
        data={
            "password": "ActualPassword123!",
            "payload_type": "text",
            "payload_text": "Sensitive intel",
        },
        files={"cover_file": ("cover.png", cover_image_bytes, "image/png")},
    )
    stego_dl = client.get(embed_res.json()["download_url"])
    stego_bytes = stego_dl.content

    # Attempt extraction with wrong password
    extract_res = client.post(
        "/api/v1/stego/extract",
        data={"password": "AttackerWrongPassword456!"},
        files={"stego_file": ("stego.png", stego_bytes, "image/png")},
    )
    assert extract_res.status_code == 400
    assert extract_res.json()["detail"] == "WRONG_PASSWORD_OR_NO_DATA"


def test_extract_clean_cover_uniform_error(client: TestClient, cover_image_bytes: bytes) -> None:
    extract_res = client.post(
        "/api/v1/stego/extract",
        data={"password": "SomePassword123!"},
        files={"stego_file": ("clean_cover.png", cover_image_bytes, "image/png")},
    )
    assert extract_res.status_code == 400
    assert extract_res.json()["detail"] == "WRONG_PASSWORD_OR_NO_DATA"


def test_analyze_compare_endpoint(client: TestClient, cover_image_bytes: bytes) -> None:
    # 1. Embed to get a stego image
    embed_res = client.post(
        "/api/v1/stego/embed",
        data={
            "password": "Password123!",
            "payload_type": "text",
            "payload_text": "Analyze test payload",
        },
        files={"cover_file": ("cover.png", cover_image_bytes, "image/png")},
    )
    stego_bytes = client.get(embed_res.json()["download_url"]).content

    # 2. Analyze comparison
    analyze_res = client.post(
        "/api/v1/stego/analyze",
        files={
            "cover_file": ("cover.png", cover_image_bytes, "image/png"),
            "stego_file": ("stego.png", stego_bytes, "image/png"),
        },
    )
    assert analyze_res.status_code == 200
    data = analyze_res.json()
    assert "mse" in data
    assert "psnr" in data
    assert "ssim" in data
    assert "heatmap_url" in data
    assert "bitplane_url" in data
    assert "pov_histogram" in data

    # Verify heatmap and bitplane are downloadable
    hm_res = client.get(data["heatmap_url"])
    assert hm_res.status_code == 200
    bp_res = client.get(data["bitplane_url"])
    assert bp_res.status_code == 200


def test_analyze_dimension_mismatch(client: TestClient, cover_image_bytes: bytes) -> None:
    # Create smaller image 32x32
    small_img = Image.new("RGB", (32, 32), color=(100, 100, 100))
    buf = io.BytesIO()
    small_img.save(buf, format="PNG")
    small_bytes = buf.getvalue()

    res = client.post(
        "/api/v1/stego/analyze",
        files={
            "cover_file": ("cover.png", cover_image_bytes, "image/png"),
            "stego_file": ("small.png", small_bytes, "image/png"),
        },
    )
    assert res.status_code == 400
    assert "dimensions do not match" in res.json()["detail"]


def test_detect_stego_endpoint(client: TestClient, cover_image_bytes: bytes) -> None:
    detect_res = client.post(
        "/api/v1/stego/detect",
        files={"image_file": ("candidate.png", cover_image_bytes, "image/png")},
    )
    assert detect_res.status_code == 200
    data = detect_res.json()
    assert "operation_id" in data
    assert "chi_square" in data
    assert "rs_analysis" in data
    assert data["classification"] in ("clean", "suspicious", "likely_stego")
