# StegaShield — Viva Defense & Technical Reference Notes (Draft v1.0)

**Subject:** Information and Network Security  
**Project:** StegaShield — Steganography & Steganalysis Lab  
**Student:** Prem, Final-Year ISE  
**Phase:** Phase 1 Core Library & Literature Reference

---

## 1. Executive Summary & Core Definitions

### What is the core difference between Cryptography and Steganography?
- **Cryptography** protects the *confidentiality* and *integrity* of the message content. An adversary can clearly see that communication is taking place (the ciphertext looks like random noise), but cannot read it without the decryption key.
- **Steganography** conceals the *very existence* of the communication. The secret payload is embedded inside an innocent cover medium (such as a PNG image) so that an eavesdropper does not suspect a secret is present.
- **Core Security Axiom**: *Hiding is not security.* If an adversary suspects an image and extracts the raw bits, pure steganography provides zero confidentiality. Therefore, StegaShield always authenticates and encrypts the payload before embedding.

---

## 2. Cryptographic Architecture

### Key Derivation: scrypt (RFC 7914 / OWASP)
- **Parameters**: $N = 131072$ ($2^{17}$ iterations), $r = 8$ (block size), $p = 1$ (parallelization), $\text{dklen} = 32$ bytes.
- **Why scrypt instead of PBKDF2 or SHA-256?**
  - PBKDF2 is CPU-intensive but requires virtually no memory, making it vulnerable to massive hardware acceleration on GPUs and ASICs.
  - scrypt is **memory-hard** ($\approx 128\text{ MiB}$ of RAM required per derivation). This drastically raises the hardware cost of parallel brute-force attacks on user passwords.

### Key Separation: HKDF-SHA256 (RFC 5869)
- **Never reuse a key for two distinct purposes.**
- From the master key derived by scrypt, StegaShield derives two cryptographically independent keys using HKDF-Expand with distinct domain info strings:
  1. `enc_key` (`b"stegashield-aes256gcm-encryption"`): 32-byte key exclusively for AES-256-GCM.
  2. `perm_key` (`b"stegashield-prng-permutation"`): 32-byte key exclusively for seeding the PRNG permutation.

### Authenticated Encryption: AES-256-GCM
- **Primitive**: Galois/Counter Mode (GCM) authenticated encryption with a 12-byte random nonce and 16-byte authentication tag.
- **Associated Authenticated Data (AAD)**: The 4-byte big-endian ciphertext length is bound into the AAD. Any tampering with the ciphertext length or ciphertext bits causes the GCM tag verification to fail immediately.
- **Uniform Error Handling**: If decryption fails (due to wrong password, absent payload, or altered stego bits), StegaShield always raises a single uniform error: `WRONG_PASSWORD_OR_NO_DATA`. This prevents padding oracles, tag timing leaks, and confirmation of hidden payload presence.

---

## 3. Steganographic Embedding & Extraction

### Cover Representation & Capacity
- Cover capacity in bits is $3 \times W \times H$ (1 bit per RGB color channel sample in raster scan order).
- **Sequential Prefix (Slots 0..127)**: Holds the 16-byte random salt. Because the salt is needed to run scrypt and derive keys, it must be located at a deterministic, key-independent position.
- **Permuted Body (Slots 128..Capacity-1)**: Shuffled using a deterministic PRNG seeded by `perm_key`. This disperses the payload evenly across the spatial domain rather than clustering it at the top-left corner.

### Embedding Methods

#### 1. LSB Replacement
- **Formula**: $\text{sample}' = (\text{sample} \ \& \ \sim 1) \ | \ \text{bit}$ (or using bitwise `(sample & 0xFE) | bit` in uint8).
- **Mechanism**: The least significant bit is directly overwritten by the payload bit.
- **Vulnerability**: Modifying the LSB exchanges values within fixed Pairs of Values (PoVs) $(2k, 2k+1)$. This causes measurable equalization in the image histogram, making it detectable by Chi-Square and RS steganalysis.

#### 2. LSB Matching ($\pm 1$ Embedding)
- **Formula**:
  - If $\text{sample} \ \& \ 1 == \text{bit}$: leave $\text{sample}$ unchanged.
  - If $\text{sample} \ \& \ 1 \ne \text{bit}$: randomly add $+1$ or $-1$ with probability $0.5$.
  - Clamping: At 0 use $+1$; at 255 use $-1$.
- **Why is it superior?** Because changes cross pair boundaries ($2k-1 \leftrightarrow 2k \leftrightarrow 2k+1$), LSB matching **does not equalize pairs of values**. It evades Chi-Square analysis completely and significantly degrades RS analysis detection.

---

## 4. Steganalysis Detectors

### Chi-Square Attack (Westfeld & Pfitzmann, 2000)
- **Invariant**: In clean natural images, adjacent frequency pairs $n(2k)$ and $n(2k+1)$ are unequal due to natural gradients. Random LSB replacement equalizes them towards their average $n^*(k) = \frac{n(2k) + n(2k+1)}{2}$.
- **Statistic**:
  $$\chi^2 = \sum_{k \in \text{valid}} \frac{(n(2k) - n(2k+1))^2}{2 n^*(k)}, \quad df = \text{valid\_pairs} - 1$$
- **Cochran's Rule**: Discards pairs where $n^*(k) < 4.0$ to ensure statistical validity.
- **Score**: $p = \text{scipy.stats.chi2.sf}(\chi^2, df)$. A $p \approx 1.0$ indicates equalized pairs (LSB replacement stego); $p \approx 0.0$ indicates natural inequality (clean or LSB matching).
- **Honest Viva Note**: With randomized permutation, Chi-square only reliably detects **high payload ratios** ($\ge 50\%-100\%$). Low payloads leave enough untouched natural pairs that the global chi-square statistic remains high.

### RS Analysis (Fridrich, Goljan, Du, 2001)
- **Grouping**: Groups of $n=4$ consecutive pixels.
- **Discrimination Function**: $f(G) = \sum_{i=1}^{n-1} |x_{i+1} - x_i|$ (measures local noisiness).
- **Dual Masks & Flipping**: $M = [0, 1, 1, 0]$ and $-M = [0, -1, -1, 0]$ with $F_1(x) = x \oplus 1$ and $F_{-1}(x) = x \mp 1$.
- **Quadratic Modeling**: Counts regular ($f(F_M) > f$) and singular ($f(F_M) < f$) groups on the image and on the LSB-flipped image, then solves:
  $$2(d_1 + d_0) x^2 + (d_{-0} - d_{-1} - d_1 - 3d_0) x + (d_0 - d_{-0}) = 0$$
- **Estimated Ratio**: $\hat{p} = \left| \frac{x}{x - 0.5} \right|$ clamped to $[0.0, 1.0]$.
- **Honest Viva Note**: RS analysis is highly sensitive to LSB replacement (detecting even partial payloads), but is less effective against LSB matching.

---

## 5. Image Quality Metrics: PSNR vs SSIM

- **MSE (Mean Squared Error)**: Arithmetic average of squared pixel intensity differences across all channels.
- **PSNR (Peak Signal-to-Noise Ratio)**:
  $$\text{PSNR} = 10 \cdot \log_{10}\left(\frac{255^2}{\text{MSE}}\right)$$
  - Steganography typically yields PSNR $> 50\text{ dB}$, which is completely imperceptible to the human eye.
- **SSIM (Structural Similarity Index)**: Measures luminance, contrast, and structural correlation using Gaussian windowing (Wang et al., 2004). Stego images typically achieve $\text{SSIM} > 0.999$.
- **Viva Warning**: High PSNR/SSIM does NOT prove steganographic security! It only proves that the changes are invisible to human vision. Statistical detectors detect the mathematical artifacts regardless of invisibility.

---

## 6. Top 20 Viva Questions & Model Answers

1. **Q: Why can't we use standard AES-CBC with a user password directly?**  
   *A:* Passwords have low entropy and can be easily dictionary-attacked without a slow, salted KDF like scrypt. Furthermore, CBC mode does not provide built-in ciphertext integrity authentication (which GCM provides via its GMAC tag).

2. **Q: What is the purpose of the 128-position sequential salt prefix?**  
   *A:* To derive the keys, the server must know the salt. If the salt were scattered with the permuted body, we would need the key to find the salt—a circular dependency. The prefix breaks this cycle cleanly.

3. **Q: Why does LSB replacement fail Chi-Square analysis at high payloads?**  
   *A:* LSB replacement only swaps the least significant bit between $2k$ and $2k+1$. Because ciphertext bits are uniformly distributed ($50\%$ 0, $50\%$ 1), it mathematically equalizes the counts of $2k$ and $2k+1$.

4. **Q: Why does LSB matching evade Chi-Square analysis?**  
   *A:* Instead of purely flipping the LSB, LSB matching adds $+1$ or $-1$. This causes transitions across pair boundaries ($2k \leftrightarrow 2k-1$), preventing the equalization of pairs of values.

5. **Q: What does a Chi-Square p-value of 0.9999 mean?**  
   *A:* It means the observed pairs of values are so unnaturally equalized that the probability of seeing such equalized pairs in a natural image by pure chance is less than $0.01\%$. It indicates LSB replacement steganography.

6. **Q: Why does StegaShield only output PNG images, never JPEG?**  
   *A:* JPEG uses lossy discrete cosine transform (DCT) compression and quantization, which completely destroys spatial LSB modifications. PNG uses lossless DEFLATE compression, perfectly preserving pixel bits.

7. **Q: Why does StegaShield return the exact same error for wrong password and clean image?**  
   *A:* Uniform error handling (`WRONG_PASSWORD_OR_NO_DATA`) prevents an attacker from determining whether a steganographic message exists in the image.

8. **Q: What is Cochran's rule in Chi-Square steganalysis?**  
   *A:* The continuous $\chi^2$ distribution approximation becomes inaccurate if expected bin counts are very small. Cochran's rule filters out pairs where expected frequency $< 4$, preventing division by near-zero and false alarms.

9. **Q: Does a PSNR of 60 dB mean the steganography is secure?**  
   *A:* No. PSNR measures human visual perception. Statistical detectors (like Chi-Square and RS analysis) operate on statistical distributions, easily detecting modifications that human eyes cannot see.

10. **Q: What are the primary limitations of non-adaptive spatial steganography?**  
    *A:* Non-adaptive methods modify pixels uniformly regardless of image content (flat skies vs textured trees). Modern steganalysis can easily detect uniform changes. Advanced steganography uses content-adaptive methods (such as S-UNIWARD or WOW) to hide data only in complex textures.

11. **Q: What is the role of HKDF-SHA256 in StegaShield?**  
    *A:* HKDF provides cryptographic key separation. It derives two mathematically independent 256-bit keys from the single scrypt master key: `enc_key` for AES-GCM and `perm_key` for PRNG permutation seeding, avoiding key reuse vulnerabilities.

12. **Q: Why is PRNG permutation used instead of sequential embedding?**  
    *A:* Sequential embedding clusters changes at the top-left corner of the image, creating a sharp localized statistical anomaly. PRNG permutation disperses modifications uniformly across the entire spatial domain.

13. **Q: How does RS analysis distinguish between clean and stego images?**  
    *A:* RS analysis groups pixels into blocks and measures variation under positive and negative flipping masks. In clean images, the counts of regular groups ($R_M$ and $R_{-M}$) are approximately equal. LSB replacement disturbs this symmetry in a predictable quadratic curve that allows estimating the embedded payload ratio.

14. **Q: What is the difference between PSNR and SSIM?**  
    *A:* PSNR computes pure pixel-by-pixel mean squared error (intensity difference) irrespective of spatial structure. SSIM (Structural Similarity) models human visual perception by measuring luminance, contrast, and structural degradation across local Gaussian windows.

15. **Q: What happens if an adversary modifies a single pixel in a StegaShield stego image?**  
    *A:* If the pixel modified falls within the embedded payload positions, the AES-256-GCM authentication tag verification will fail upon extraction, and the system safely rejects the payload with `WRONG_PASSWORD_OR_NO_DATA`.

16. **Q: Why is the ciphertext length bound-checked before memory allocation?**  
    *A:* To prevent memory exhaustion (DoS attacks). A crafted stego image could declare an enormous ciphertext length ($2^{32}-1$ bytes); checking it against the image's physical capacity before allocation prevents allocating gigabytes of RAM.

17. **Q: How does StegaShield calibrate detector thresholds without hardcoding magic numbers?**  
    *A:* StegaShield runs an empirical calibration script (`scripts/calibrate_thresholds.py`) on clean baseline images. The 95th percentile score is set as the `suspicious` threshold, and the 99th percentile is set as the `likely_stego` threshold, resulting in a predictable $\le 5\%$ false-positive rate.

18. **Q: How are temporary files managed to prevent forensic exposure?**  
    *A:* Files are saved with random UUID filenames and tracked in a `temp_files` table with an expiration timestamp. A background cleanup worker periodically deletes all files older than 30 minutes from the server disk.

19. **Q: Why does StegaShield use AES-GCM Associated Authenticated Data (AAD)?**  
    *A:* The 4-byte ciphertext length is passed as AAD to the AES-GCM cipher. This cryptographically binds the length to the ciphertext, ensuring that an adversary cannot truncate or splice the payload without triggering a tag mismatch.

20. **Q: In an INS viva, how do you explain the Attack Lab experiment results?**  
    *A:* At low payloads ($5\%-10\%$), both Chi-Square and RS detectors show low detection rates because few samples are altered. At higher payloads ($\ge 50\%$), Chi-Square and RS detection rates on LSB replacement spike towards $100\%$, while LSB matching maintains a near-zero Chi-Square score, empirically proving the statistical superiority of $\pm 1$ embedding over bit replacement.

---

## 7. Module-by-Module Code Walkthrough for Viva

- **`backend/app/core/crypto.py`**:
  - `derive_keys(password, salt)`: Runs `hashlib.scrypt` with $N=131072, r=8, p=1$, then passes the result through two HKDF expansions.
  - `encrypt_payload(data, enc_key, is_file, filename)`: Formats container bytes `[type | fn_len | filename | data]`, binds `ct_len` into AAD, and runs `AESGCM(enc_key).encrypt`.
  - `decrypt_payload(...)`: Verifies tag, extracts fields, and raises uniform `StegaShieldError`.

- **`backend/app/core/stego.py`**:
  - `calculate_capacity(image)`: Calculates $3 \times W \times H - 400$ bits of usable space.
  - `embed(...)`: Embeds 128-bit salt sequentially into RGB channel samples $0..127$, seeds NumPy PRNG with `perm_key` to shuffle remaining slots, and applies LSB replacement (`& 0xFE | bit`) or LSB matching ($\pm 1$).
  - `extract(...)`: Reads salt from slots $0..127$, regenerates permutation, reads header, and decrypts.

- **`backend/app/core/detect.py`**:
  - `chi_square_attack(image)`: Pools 128 PoVs, filters bins where expected count $< 4$, calculates $\chi^2$ statistic, and computes SciPy survival function p-value.
  - `rs_analysis(image)`: Fully vectorized calculation of regular/singular groups under masks $[0,1,1,0]$ and $[0,-1,-1,0]$, solving the quadratic equation to estimate embedded ratio $\hat{p}$.

- **`backend/app/core/metrics.py`**:
  - `calculate_metrics(cover, stego)`: Computes MSE, PSNR, and vectorized 3D SSIM using SciPy's `gaussian_filter` across spatial axes without color distortion.
  - `generate_diff_heatmap(...)`: Amplifies pixel differences by 255 for visual inspection.
  - `generate_bitplane(...)`: Isolates LSB plane `(arr & 1) * 255`.

