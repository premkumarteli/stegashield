# StegaShield — Steganography & Steganalysis Lab

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Next.js 15](https://img.shields.io/badge/next.js-15-black.svg)](https://nextjs.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**StegaShield** is an advanced steganography and statistical steganalysis laboratory developed for the academic subject *Information and Network Security (INS)*. 

It conceals password-encrypted, authenticated payloads (AES-256-GCM with scrypt key derivation) inside lossless PNG images using both LSB replacement and LSB matching ($\pm 1$), and attacks its own stego images with real statistical detectors (**Chi-Square Attack** and **RS Analysis**). Results are visualized in a web application designed under the **Abyssal Liquid Glass** material system.

---

## 🌟 Key Features

1. **Authenticated In-Depth Cryptography:**
   - **scrypt KDF**: Memory-hard key derivation ($N=131072, r=8, p=1$, ~128 MiB RAM) to defend against GPU/ASIC password cracking.
   - **HKDF-SHA256**: Independent key derivation for AES encryption (`enc_key`) and PRNG spatial permutation (`perm_key`).
   - **AES-256-GCM**: Authenticated encryption with 12-byte random nonce and 16-byte GMAC tag. Ciphertext length bound into Associated Authenticated Data (AAD).
   - **Uniform Error Suppression**: Identical `WRONG_PASSWORD_OR_NO_DATA` response for wrong passwords, altered bits, or absent payloads to eliminate oracle leaks.

2. **Steganographic Hiding:**
   - **LSB Replacement**: Replaces least-significant bits directly (`& 0xFE | bit`).
   - **LSB Matching ($\pm 1$)**: Adds or subtracts 1 at random with clamping at $[0, 255]$ to avoid equalizing Pairs of Values.
   - **Spatial Dispersion**: 128-bit sequential salt prefix followed by deterministic PRNG permutation across remaining RGB channels.
   - Supports PNG, JPEG, and BMP covers (up to 10 MB and 16 megapixels); output is always lossless PNG.

3. **Statistical Steganalysis Detectors:**
   - **Chi-Square Attack** (Westfeld & Pfitzmann, 2000): Tests histogram Pairs-of-Values equalization with Cochran bin filtering ($n^*(k) \ge 4$).
   - **RS Analysis** (Fridrich, Goljan, Du, 2001): 4-pixel spatial variation analysis under dual masks $M=[0,1,1,0]$ and $-M=[0,-1,-1,0]$ with quadratic root estimation.
   - **Zero-Loop Vectorization**: Fully vectorized with NumPy for sub-second execution.

4. **Interactive Attack Lab & Visual Analytics:**
   - Automated payload sweeps ($5\%, 10\%, 25\%, 50\%, 100\%$) comparing Replacement vs. Matching.
   - Before/after comparison slider, amplified difference heatmaps, LSB bit-plane viewers, and Pairs-of-Values histograms.
   - Live progress polling, false-positive rate tracking, and one-click CSV export.

5. **Abyssal Liquid Glass UI (Next.js 15):**
   - Palette: Abyss Navy (`#07131D`), Deep Ocean (`#102631`), Liquid Teal (`#36D6C3`), Ice Mint (`#91F3E6`), Frost (`#E5F1F3`).
   - Floating liquid navigation with gliding pill highlight, 4-step embed wizard with live capacity meter, and interactive LSB pixel bit-flip widget.
   - WCAG 2.2 AA accessibility with full keyboard navigation and responsive layouts from 320px to 1440px.

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                 Client Layer (Browser)                      │
│   Next.js 15 (App Router) + TypeScript Strict               │
│   Abyssal Liquid Glass Design System + Tailwind CSS         │
└──────────────────────────────┬──────────────────────────────┘
                               │ REST (JSON & Multipart)
                               ▼
┌─────────────────────────────────────────────────────────────┐
│               Presentation Layer (FastAPI)                  │
│   app/main.py, app/config.py, app/api/                      │
│   - Pydantic v2 schemas, rate limiting, CORS               │
│   - Anonymous session cookie tracking (HttpOnly, SameSite)  │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                     Service Layer                           │
│   app/services/ (embed, extract, analyze, experiment)       │
│   - file_store with automated 30-min TTL background cleanup │
└──────────────┬───────────────────────────────┬──────────────┘
               │                               │
               ▼                               ▼
┌──────────────────────────────┐ ┌────────────────────────────┐
│      Core Domain Layer       │ │      Data Access Layer     │
│   app/core/ (Pure Python)    │ │   app/db/ (SQLAlchemy 2.x) │
│   - crypto.py: scrypt + GCM  │ │   - Operation, Detection   │
│   - stego.py: replacement /  │ │   - TempFile, Experiment   │
│     matching embedding       │ │   - ExperimentRun          │
│   - metrics.py: MSE/PSNR/SSIM│ │   - Alembic migrations     │
│   - detect.py: Chi2 & RS     │ └─────────────┬──────────────┘
│   - attack_lab.py: Sweeps    │               │
└──────────────────────────────┘               ▼
                                 ┌────────────────────────────┐
                                 │      Relational Store      │
                                 │   MySQL 8.0 (InnoDB utf8mb4)│
                                 └────────────────────────────┘
```

---

## 🚀 Quick Start Guide

### Prerequisites
- **Python 3.12+**
- **Node.js (v18+)** and `npm`
- **MySQL 8.0** (or higher)

### 1. Database Setup (MySQL 8)

Log in to your MySQL terminal and run:

```sql
CREATE DATABASE stegashield CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'stegashield'@'localhost' IDENTIFIED BY 'stegashield_password';
GRANT ALL PRIVILEGES ON stegashield.* TO 'stegashield'@'localhost';
FLUSH PRIVILEGES;
```

### 2. Backend Setup

#### Windows (PowerShell):
```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp ..\.env.example .env
alembic upgrade head
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### Linux / macOS (Bash):
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example .env
alembic upgrade head
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Interactive OpenAPI documentation is available at `http://localhost:8000/docs`.

### 3. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000` in your web browser.

### 4. One-Click Launch Scripts

- **Windows:** `.\scripts\dev.ps1`
- **Linux/macOS:** `./scripts/dev.sh`

---

## 🧪 Testing & Verification

### Run Backend Unit & Integration Tests:
```bash
cd backend
# Run all 110 tests (94 core unit tests + 16 API integration tests)
python -m pytest tests/ -v
```

### Run Static Analysis:
```bash
cd backend
python -m ruff check app tests
python -m mypy --strict app/core
```

### Run Frontend Production Build:
```bash
cd frontend
npm run build
```

---

## 📊 Attack Lab Empirical Benchmark Results

Measured on standard $256 \times 256$ RGB cover images with AES-256-GCM encrypted payloads:

| Method | Payload Ratio | Payload Size | Chi-Square ($p$-value) | $\chi^2$ Statistic | RS Estimated Ratio ($\hat{p}$) | PSNR |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| `clean` | **0%** | 0 B | **0.000000** | 14,459.13 | **0.2634** | $\infty$ |
| `replacement` | **5%** | 1,226 B | **0.000000** | 13,149.44 | **0.2015** | 63.99 dB |
| `replacement` | **25%** | 6,131 B | **0.000000** | 8,217.54 | **0.0703** | 57.16 dB |
| `replacement` | **50%** | 12,263 B | **0.000000** | 3,854.78 | **0.4113** | 54.14 dB |
| `replacement` | **100%** | 24,526 B | **0.058124** | **152.96** | **0.9280** | 51.15 dB |
| `matching` | **5%** | 1,226 B | **0.000000** | 12,996.25 | **0.2195** | 64.00 dB |
| `matching` | **50%** | 12,263 B | **0.000000** | 3,313.85 | **0.0396** | 54.13 dB |
| `matching` | **100%** | 24,526 B | **0.000000** | **422.79** | **0.2401** | 51.15 dB |

*Key finding: At 100% capacity, LSB Replacement is flagged by RS analysis ($\hat{p} = 0.9280$) and shows distinct Chi-Square equalization ($p = 0.0581$). In contrast, LSB Matching completely evades Chi-Square ($p = 0.000000$) and suppresses RS estimation by >74%.*

---

## 📚 Project Documentation

- [`SPEC.md`](file:///c:/Users/prem/tmp/stegashield/SPEC.md): Master product specification.
- [`docs/ARCHITECTURE.md`](file:///c:/Users/prem/tmp/stegashield/docs/ARCHITECTURE.md): System architecture and data flow.
- [`docs/THREAT_MODEL.md`](file:///c:/Users/prem/tmp/stegashield/docs/THREAT_MODEL.md): Assets, threats, mitigations, and honest limitations.
- [`docs/DECISIONS.md`](file:///c:/Users/prem/tmp/stegashield/docs/DECISIONS.md): Architectural decision records (ADRs).
- [`docs/EXPERIMENT_REPORT.md`](file:///c:/Users/prem/tmp/stegashield/docs/EXPERIMENT_REPORT.md): Attack Lab experimental evaluation with real database data.
- [`docs/VIVA_NOTES.md`](file:///c:/Users/prem/tmp/stegashield/docs/VIVA_NOTES.md): Comprehensive viva defense notes with 20 questions and answers.

---

## 📖 Academic References

1. **A. Westfeld and A. Pfitzmann**, *"Attacks on Steganographic Systems"*, Information Hiding, Lecture Notes in Computer Science, vol. 1768, Springer, 2000.
2. **J. Fridrich, M. Goljan, and R. Du**, *"Detecting LSB Steganography in Color and Gray-Scale Images"*, IEEE Multimedia, vol. 8, no. 4, pp. 22–28, 2001.
3. **Z. Wang, A. C. Bovik, H. R. Sheikh, and E. P. Simoncelli**, *"Image Quality Assessment: From Error Visibility to Structural Similarity"*, IEEE Transactions on Image Processing, vol. 13, no. 4, pp. 600–612, 2004.
4. **W. Luo et al.**, *"A Comprehensive Survey of Digital Image Steganography and Steganalysis"*, APSIPA Transactions on Signal and Information Processing, 2024.
