# StegaShield — Architecture & System Design

## 1. High-Level System Architecture

StegaShield is designed as a decoupled, layered client-server application adhering to strict separation of concerns:

```
┌─────────────────────────────────────────────────────────────┐
│                 Client Layer (Browser)                      │
│   Next.js 15 (App Router) + TypeScript (Strict)             │
│   Tailwind CSS + Lucide Icons + TanStack Query              │
│   Abyssal Liquid Glass Design System                        │
└──────────────────────────────┬──────────────────────────────┘
                               │ REST (JSON & Multipart)
                               ▼
┌─────────────────────────────────────────────────────────────┐
│               Presentation Layer (FastAPI)                  │
│   app/main.py, app/config.py, app/api/                      │
│   - Strict request validation via Pydantic v2 schemas       │
│   - Rate limiting via slowapi                               │
│   - CORS policy & security response headers                 │
│   - Anonymous session cookie tracking (HttpOnly, SameSite)  │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                     Service Layer                           │
│   app/services/                                             │
│   - embed_service, extract_service, analyze_service         │
│   - experiment_service (background thread execution)        │
│   - file_store (TTL tracking with automated 30-min cleanup)│
└──────────────┬───────────────────────────────┬──────────────┘
               │                               │
               ▼                               ▼
┌──────────────────────────────┐ ┌────────────────────────────┐
│      Core Domain Layer       │ │      Data Access Layer     │
│   app/core/ (Pure Python)    │ │   app/db/ (SQLAlchemy 2.x) │
│   - crypto.py: scrypt + GCM  │ │   - Operation, Detection   │
│   - stego.py: LSB replacement│ │   - TempFile, Experiment   │
│     and LSB matching         │ │   - ExperimentRun          │
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

## 2. Layering Rules & Architectural Invariants

1. **Pure Core Domain (`backend/app/core/`):**
   - Pure mathematical, algorithmic, and cryptographic code.
   - Depends only on Python standard library, NumPy, SciPy, Pillow, and cryptography.
   - Zero dependencies on FastAPI, HTTP models, SQLAlchemy, or database connections.
   - Fully testable in isolation.

2. **Service Layer (`backend/app/services/`):**
   - Coordinates business workflows by combining core library functions with database repositories and temporary file management.
   - Encapsulates file storage lifecycle and session boundaries.

3. **API Layer (`backend/app/api/`):**
   - Handles HTTP transport, multipart form decoding, and response status mapping.
   - All errors are formatted as structured JSON: `{"error": {"code": "...", "message": "...", "details": {...}}}`.

4. **Data Access Layer (`backend/app/db/`):**
   - SQLAlchemy 2.0 ORM models using UTC timestamps.
   - Repositories encapsulate database queries.
   - Zero raw secrets, passwords, or cryptographic keys are ever persisted to disk or database.

5. **Frontend Client (`frontend/`):**
   - Built with Next.js 15 App Router and React.
   - Interacts with backend via strongly typed OpenAPI client generated from FastAPI schema.
   - UI reflects strictly real measured values from API calls.

---

## 3. Database Schema Design (MySQL 8)

The schema consists of five normalized tables:

1. **`operations`**:
   - Primary log of user actions (`embed`, `extract`, `detect`, `compare`).
   - Stores image dimensions, SHA-256 hashes, payload sizes, capacity, and quality metrics (MSE, PSNR, SSIM).
   - Indexed by `session_id` and `created_at`.

2. **`detections`**:
   - Individual detector scores (`chi_square`, `rs`), thresholds, and categorical verdicts (`clean`, `suspicious`, `likely_stego`).
   - Foreign key to `operations.id` with cascade deletion.

3. **`temp_files`**:
   - Manages temporary cover, stego, difference heatmap, and bitplane PNGs.
   - Indexed by `expires_at` for high-performance background TTL cleanup.

4. **`experiments`**:
   - Attack Lab experiment configurations, progress percentage, execution status, and timing.

5. **`experiment_runs`**:
   - Granular data points for each payload ratio and embedding method evaluated during an experiment.
   - Composite index on `(experiment_id, method, payload_ratio)` for fast aggregation queries.
