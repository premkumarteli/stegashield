# Project: StegaShield

StegaShield is an academic-grade steganography and steganalysis experimentation laboratory. It features authenticated encrypted LSB steganography (LSB replacement and LSB matching), quantitative distortion metrics, statistical steganalysis detectors (Chi-square and RS analysis), an automated Attack Lab empirical matrix engine, a production FastAPI/SQLAlchemy backend, and a modern Next.js 15 frontend.

## Architecture

- **Core Engine (`backend/app/core/`)**: Pure domain logic with zero web or database dependencies. Strict type annotations, NumPy 2.x and SciPy vectorized mathematical operations.
  - `crypto.py`: Scrypt KDF, HKDF-SHA256, AES-256-GCM, uniform error suppression.
  - `stego.py`: LSB replacement, LSB matching, PRNG pseudo-random permutation embedding, capacity checking.
  - `metrics.py`: MSE, PSNR, SSIM (Gaussian filtered), difference heatmaps, bitplane visualization, PoV histograms.
  - `detect.py`: Westfeld & Pfitzmann (2000) Chi-square attack, Fridrich, Goljan, Du (2001) RS analysis, classification.
  - `attack_lab.py`: Matrix experimentation runner across methods, payload ratios, and detectors; RFC 4180 CSV export.
- **Backend API & Data Layer (`backend/app/`)**:
  - `config.py`: Pydantic-settings configuration with environment variable loading.
  - `db/models.py`: SQLAlchemy 2.x ORM models (`operations`, `detections`, `temp_files`, `experiments`, `experiment_items`). Zero secrets persisted.
  - `db/session.py`: Async/sync engine with connection recycling and fallback to SQLite for test isolation.
  - `db/repositories.py`: Data access repositories.
  - `schemas/`: Pydantic v2 validation models.
  - `services/`: `embed_service`, `extract_service`, `analyze_service`, `experiment_service` (with single-experiment mutex), `file_store` (TTL 30min cleanup).
  - `api/`: FastAPI route routers for health, embed, extract, analyze, experiments, history, files.
- **Frontend Layer (`frontend/`)**:
  - Next.js 15 App Router, TypeScript (strict), Tailwind CSS, shadcn/ui.
  - Dark theme default with WCAG 2.1 AA compliant tokens.
  - Pages: `/` (Landing & interactive 8-bit LSB widget), `/embed` (4-step wizard), `/extract` (Extraction), `/analyze` (Compare & Detect), `/attack-lab` (Attack Lab sweep & live progress), `/history` (Session operations), `/about` (Architecture & academic threat model).
  - Strongly typed client generated from FastAPI OpenAPI schema via `openapi-typescript` + `openapi-fetch`.
- **E2E Test Infrastructure (`tests/e2e/`)**:
  - Multi-adapter client: `direct_core`, `asgi_testclient`, `live_http`.
  - 4-Tier verification: Tier 1 (Feature Coverage), Tier 2 (Boundary & Corner), Tier 3 (Cross-Feature Pairwise), Tier 4 (Real-World Workloads).

## Feature Inventory

| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | Scrypt KDF & Key Separation | Scrypt N=2^17, r=8, p=1; HKDF-SHA256 separating enc_key and perm_key | M1 | Survey / `crypto.py` |
| 2 | AES-256-GCM Encryption | Authenticated symmetric encryption with AAD binding ciphertext length | M1 | Survey / `crypto.py` |
| 3 | Uniform Error Suppression | Raises uniform `StegaShieldError("WRONG_PASSWORD_OR_NO_DATA")` | M1 | Survey / `crypto.py` |
| 4 | Cover Image Validation | Supports RGB, RGBA, L modes; enforces <= 16MP limit | M1 | Survey / `stego.py` |
| 5 | Capacity Calculation | Pre-allocation capacity verification ensuring payload fits total slots | M1 | Survey / `stego.py` |
| 6 | PRNG Permutation Embedding | Sequential 128-bit salt prefix followed by PRNG permuted slots | M1 | Survey / `stego.py` |
| 7 | LSB Replacement | Bitwise mask embedding replacing lowest bit with payload bit | M1 | Survey / `stego.py` |
| 8 | LSB Matching (±1) | Randomly adjusts pixel ±1, clamped to [0, 255] | M1 | Survey / `stego.py` |
| 9 | Distortion Metrics | Vectorized MSE, PSNR, SSIM, Diff Heatmap, Bitplane, PoV Histogram | M1 | Survey / `metrics.py` |
| 10 | Chi-Square Steganalysis | Westfeld & Pfitzmann (2000) 128 PoVs, Cochran filter (>=4), SciPy chi2.sf | M2 | Survey / `detect.py` |
| 11 | RS Steganalysis | Fridrich et al. (2001) 4-pixel groups, M and -M masks, quadratic root solver, channel mean | M2 | Survey / `detect.py` |
| 12 | Threshold Calibration | Script scoring clean images to derive 95th/99th percentiles into `config/thresholds.json` | M2 | Survey / `scripts/calibrate_thresholds.py` |
| 13 | Attack Lab Matrix Engine | Sweeps methods x ratios x detectors, tracking detection and false-positive rates | M2 | Survey / `attack_lab.py` |
| 14 | Attack Lab CSV Export | RFC 4180 CSV export with 7 mandatory columns | M2 | Survey / `attack_lab.py` |
| 15 | FastAPI Application & Config | FastAPI app with pydantic-settings, CORS, rate limiting via slowapi, security headers | M3 | Survey / `backend/app/main.py` |
| 16 | Database Schema & Alembic | MySQL 8 / SQLite SQLAlchemy 2.x models: operations, detections, temp_files, experiments, experiment_items | M3 | Survey / `backend/app/db/` |
| 17 | Anonymous Session Management | UUIDv4 session cookie (HttpOnly, SameSite=Lax), scoped history | M3 | Survey / `backend/app/api/` |
| 18 | Attack Lab Mutex | Thread/async lock rejecting concurrent experiment requests with HTTP 409 | M3 | Survey / `backend/app/services/` |
| 19 | TTL File Storage & Cleanup | Temp files with 30-minute expiration countdown and automatic cleanup worker | M3 | Survey / `backend/app/services/` |
| 20 | REST API Routers | Endpoints for embed, extract, analyze, detect, attack-lab, history, files, health | M3 | Survey / `backend/app/api/` |
| 21 | Next.js App Shell & Navigation | 7 core routes: `/`, `/embed`, `/extract`, `/analyze`, `/attack-lab`, `/history`, `/about` | M4 | Survey / `frontend/` |
| 22 | Dark Theme & Design Tokens | Default dark theme with WCAG 2.1 AA contrast compliance | M4 | Survey / `frontend/` |
| 23 | Interactive 8-Bit Pixel Widget | Interactive bit-flipping visualizer demonstrating imperceptible LSB change | M4 | Survey / `frontend/` |
| 24 | 4-Step Embed Wizard | Cover upload, text/file payload, password meter, method selector, split slider | M4 | Survey / `frontend/` |
| 25 | Extract Page | Stego dropzone, error handling, text display / file download | M4 | Survey / `frontend/` |
| 26 | Analyze Dashboard | Dual tabs: Compare (heatmap, bitplane, PoV) and Detect (radial gauges, verdicts) | M4 | Survey / `frontend/` |
| 27 | Attack Lab Dashboard & SSE | Real-time SSE experiment progress, Recharts detection curves, CSV download | M4 | Survey / `frontend/` |
| 28 | Typed OpenAPI Client | Client generation via `openapi-typescript` + `openapi-fetch` | M4 | Survey / `frontend/src/lib/` |
| 29 | Academic Documentation | Architecture, Decisions, Threat Model, Viva Notes, Experiment Report, README | M5 | Survey / `docs/` |
| 30 | Cross-Platform Run Scripts | `scripts/dev.ps1` and `scripts/dev.sh` | M5 | Survey / `scripts/` |

## Milestones

| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | Core Stego, Crypto & Metrics | `crypto.py`, `stego.py`, `metrics.py`, unit tests | None | DONE |
| M2 | Steganalysis Detectors & Attack Lab Engine | `detect.py`, `attack_lab.py`, calibration script, unit tests | M1 | IN_PROGRESS |
| M3 | Backend API, Database & Services | FastAPI app, config, DB models, Alembic, services, API routers, API tests | M2 | PLANNED |
| M4 | Next.js Frontend & UI Integration | Next.js 15 App Router, Tailwind, shadcn, all 7 routes, typed client | M3 | PLANNED |
| M5 | Documentation, Full Verification & Push | Architecture docs, Threat Model, Viva Notes, scripts, git commit & push | M4 | PLANNED |

## Interface Contracts

### M2: Detectors Interface
- `chi_square_attack(image: Image.Image, channel: str = "all") -> dict[str, Any]`
  - Returns: `{"chi2": float, "p_value": float, "df": int, "classification": str, "details": dict}`
- `rs_analysis(image: Image.Image) -> dict[str, Any]`
  - Returns: `{"estimated_payload_ratio": float, "regular_m": float, "singular_m": float, "regular_neg_m": float, "singular_neg_m": float, "classification": str, "channel_ratios": dict}`
- `classify(chi2_res: dict[str, Any], rs_res: dict[str, Any], thresholds: dict[str, Any] | None = None) -> str`
  - Returns: `"clean"`, `"suspicious"`, or `"likely_stego"`
- `run_experiment(cover_images: list[Image.Image], methods: list[str], ratios: list[float], detectors: list[str]) -> dict[str, Any]`
  - Returns: experiment summary with `total_items`, `methods`, `ratios`, `detectors`, and `items`
- `export_csv(summary: dict[str, Any]) -> str`
  - Returns: RFC 4180 CSV string with 7 mandatory columns

### M3: Backend API Endpoints (OpenAPI / JSON)
- `POST /api/v1/stego/embed` (Multipart: cover_file, payload_type, payload_data/file, password, method) -> `{operation_id, download_url, metrics}`
- `POST /api/v1/stego/extract` (Multipart: stego_file, password) -> `{payload_type, payload_text, filename, download_url}` or 400 `WRONG_PASSWORD_OR_NO_DATA`
- `POST /api/v1/stego/analyze` (Multipart: cover_file, stego_file) -> `{mse, psnr, ssim, heatmap_url, bitplane_url, pov_histogram}`
- `POST /api/v1/stego/detect` (Multipart: image_file) -> `{chi_square: {...}, rs_analysis: {...}, classification: str}`
- `POST /api/v1/attack-lab/run` (JSON or Multipart: config) -> returns 409 if active experiment running, else starts run
- `GET /api/v1/attack-lab/progress/{experiment_id}` -> SSE stream (`event: progress`)
- `GET /api/v1/attack-lab/export/{experiment_id}` -> text/csv download
- `GET /api/v1/history` -> `{operations: [...]}`
- `DELETE /api/v1/history` -> `{cleared: bool}`
- `GET /api/v1/files/{file_id}` -> File stream with 30min TTL check

### M4: Frontend - Backend Client Contract
- Generated client: `frontend/src/lib/api-types.ts` via `openapi-typescript` targeting `/openapi.json`
- Base fetch client: `frontend/src/lib/api-client.ts` using `openapi-fetch` with credentials `'include'` for session cookie

## Code Layout

```
stegashield/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── crypto.py
│   │   │   ├── stego.py
│   │   │   ├── metrics.py
│   │   │   ├── detect.py          <-- M2
│   │   │   ├── detectors.py       <-- M2 alias
│   │   │   └── attack_lab.py      <-- M2
│   │   ├── db/
│   │   │   ├── __init__.py
│   │   │   ├── models.py          <-- M3
│   │   │   ├── session.py         <-- M3
│   │   │   └── repositories.py    <-- M3
│   │   ├── schemas/               <-- M3
│   │   ├── services/              <-- M3
│   │   └── api/                   <-- M3
│   ├── tests/
│   │   ├── conftest.py
│   │   ├── test_crypto.py
│   │   ├── test_stego.py
│   │   ├── test_metrics.py
│   │   ├── test_detect.py         <-- M2
│   │   ├── test_attack_lab.py     <-- M2
│   │   └── api/                   <-- M3
│   ├── alembic/                   <-- M3
│   ├── alembic.ini                <-- M3
│   ├── requirements.txt
│   └── pytest.ini
├── frontend/                      <-- M4
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx
│   │   │   ├── embed/page.tsx
│   │   │   ├── extract/page.tsx
│   │   │   ├── analyze/page.tsx
│   │   │   ├── attack-lab/page.tsx
│   │   │   ├── history/page.tsx
│   │   │   └── about/page.tsx
│   │   ├── components/
│   │   └── lib/
│   ├── package.json
│   ├── tsconfig.json
│   └── tailwind.config.ts
├── config/
│   └── thresholds.json            <-- M2
├── scripts/
│   ├── calibrate_thresholds.py    <-- M2
│   ├── dev.ps1                    <-- M5
│   └── dev.sh                     <-- M5
├── docs/                          <-- M5
│   ├── ARCHITECTURE.md
│   ├── DECISIONS.md
│   ├── THREAT_MODEL.md
│   ├── VIVA_NOTES.md
│   └── EXPERIMENT_REPORT.md
├── tests/
│   └── e2e/                       <-- Verified E2E Harness
└── README.md                      <-- M5
```
