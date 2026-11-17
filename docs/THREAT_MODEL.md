# StegaShield — Threat Model & Security Architecture

## 1. Assets & Security Boundaries

| Asset | Sensitivity | Protection Mechanism |
|---|---|---|
| User Payload (Plaintext) | Confidential | In-memory only; encrypted with AES-256-GCM before embedding. Never persisted to DB or logs. |
| User Passwords | Confidential | In-memory only; hashed via scrypt ($N=2^{17}$) with unique 16-byte random salt. Never logged or stored. |
| Cryptographic Keys | Confidential | Ephemeral in-memory derivation; separated via HKDF-SHA256 (`enc_key` vs `perm_key`). |
| Stego Images | Integrity/Confidentiality | Lossless PNG format; authenticated via AES-GCM tag on extraction. |
| System Server Integrity | High | Strict upload limits (10 MB, 16 MP), decompression bomb prevention, rate limiting. |

---

## 2. Threat Analysis & Mitigations

### 2.1 Malicious Files & Decompression Bombs
- **Threat**: An adversary uploads a massive or crafted image file (decompression bomb or malformed headers) attempting Denial of Service (DoS) or Remote Code Execution.
- **Mitigation**:
  - `MAX_UPLOAD_MB` (10 MB) enforced at the reverse proxy/HTTP transport layer before full reading.
  - Image dimension bounds enforced before full decompression (`MAX_IMAGE_PIXELS = 16_000_000`).
  - Pillow's `Image.MAX_IMAGE_PIXELS` safety threshold set.
  - All input images are decoded and re-encoded into fresh, sanitized PNG files. Client MIME types and file extensions are never trusted.

### 2.2 Brute-Force & Dictionary Attacks
- **Threat**: An attacker attempts to guess user passwords against a stego image.
- **Mitigation**:
  - **Memory-Hard KDF**: scrypt configured with $N=131072$ ($2^{17}$ iterations), $r=8$, $p=1$, requiring ~128 MiB RAM per derivation. This imposes severe memory costs on GPU/ASIC parallel cracking farms.
  - **Rate Limiting**: `slowapi` enforces request rate limits on sensitive endpoints (`/api/v1/extract` and `/api/v1/embed`).

### 2.3 Oracle & Side-Channel Leaks
- **Threat**: An attacker observes different error responses (e.g. "Wrong Password" vs "No Data Present" vs "Tag Mismatch") to probe whether an image contains a hidden message.
- **Mitigation**:
  - **Uniform Error Suppression**: Any failure during extraction—whether wrong password, corrupted ciphertext, altered stego bits, or absence of payload—returns the identical error: `WRONG_PASSWORD_OR_NO_DATA` with HTTP 400.
  - No timing or error discrimination is leaked to the client.

### 2.4 Cryptographic Tampering
- **Threat**: An adversary modifies bits in transit hoping to alter the decrypted message or induce malleable execution.
- **Mitigation**:
  - **Authenticated Encryption**: AES-256-GCM guarantees ciphertext authenticity. The 4-byte ciphertext length is included in the Associated Authenticated Data (AAD). Any modification to the stego bits causes GMAC tag validation to fail immediately.

### 2.5 Data Left on Disk
- **Threat**: Temporary uploaded or generated images remain on disk indefinitely, risking unauthorized forensic recovery.
- **Mitigation**:
  - Automated background task runs every 5 minutes in FastAPI, purging all temporary files older than `FILE_TTL_MINUTES` (30 minutes).

---

## 3. Known Limitations & Academic Honest Disclosures

1. **Hiding is Not Security**:
   Steganography only conceals the existence of a message. If the cover is analyzed by a statistical detector and the payload is discovered, security relies entirely on the strength of the AES-256-GCM encryption and the user's password entropy.
2. **Lossy Compression Fragility**:
   LSB embedding does not survive lossy compression (such as JPEG re-encoding), aggressive spatial filtering, or image resizing.
3. **Non-Adaptive Detection Vulnerability**:
   Non-adaptive spatial steganography embeds bits uniformly across the image. As demonstrated in our Attack Lab, LSB replacement is detectable at high payloads by Chi-Square and RS analysis. Modern secure steganography requires content-adaptive methods (such as S-UNIWARD, WOW, or HUGO) which place changes exclusively in complex texture regions.
4. **No Forward Secrecy or Sender Authentication**:
   The current container architecture does not support digital signatures or public-key forward secrecy; it provides symmetric password-based authenticated privacy.
