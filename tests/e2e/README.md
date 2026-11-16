# StegaShield End-to-End (E2E) Test Suite

## Overview
The StegaShield E2E test suite provides rigorous, requirement-driven, opaque-box testing of the StegaShield steganography and steganalysis platform.

It is structured into four distinct testing tiers:
- **Tier 1: Feature Coverage** (140 tests, $\ge 5$ happy-path tests across Features 1–28)
- **Tier 2: Boundary & Corner Cases** (65 tests across 12 boundary domains)
- **Tier 3: Cross-Feature Combinations** (25 tests covering pairwise subsystem interactions)
- **Tier 4: Real-World Scenarios** (5 complex operational workflows across 32 steps)

---

## Progressive Testability: Client Abstraction Layer
The E2E test suite decouples test authoring from specific runtime environments via the `StegaShieldClient` abstraction:
1. **`live_http`**: Full black-box network testing against a live FastAPI server (`httpx.Client` calling `http://127.0.0.1:8000`).
2. **`asgi_testclient`**: In-memory HTTP testing via Starlette `TestClient(app)` without network sockets.
3. **`direct_core`**: Fallback adapter importing pure Python `backend.app.core` modules directly.
4. **`auto`** (default): Automatically detects the highest available operational tier:
   `Live HTTP` $\to$ `ASGI TestClient` $\to$ `Direct Core`.

---

## Standalone Test Runner (`run_e2e.py`)

Run tests via the standalone CLI runner:

```bash
# Run Tier 1 tests (default)
python tests/e2e/run_e2e.py

# Run all test tiers
python tests/e2e/run_e2e.py --all

# Run specific tiers
python tests/e2e/run_e2e.py --tier 1
python tests/e2e/run_e2e.py --tier 1,2

# Execute against specific client adapter mode
python tests/e2e/run_e2e.py --mode direct_core
python tests/e2e/run_e2e.py --mode asgi_testclient
python tests/e2e/run_e2e.py --mode live_http --url http://127.0.0.1:8000

# Fast run (excludes slow 16MP covers)
python tests/e2e/run_e2e.py --quick

# Generate structured JSON and JUnit XML reports
python tests/e2e/run_e2e.py --all --json-report tests/e2e/reports/e2e_summary.json --junit-xml tests/e2e/reports/junit_e2e.xml

# Run environment health check
python tests/e2e/run_e2e.py --env-check
```

### Exit Codes
- `0`: All executed tests passed cleanly.
- `1`: One or more tests failed.
- `2`: Interrupted by user (SIGINT).
- `3`: Harness environment/configuration error.
- `4`: Invalid arguments.
- `5`: No tests collected.

---

## Native Pytest Invocation

You can also run tests directly with `pytest`:

```bash
# Execute Tier 1 tests
pytest tests/e2e -m tier1 -v

# Execute by custom mode
pytest tests/e2e -m tier1 --e2e-mode=direct_core

# Skip slow tests
pytest tests/e2e -m "not slow"
```

---

## Procedural Fixture Generators
To avoid binary asset bloat and version drift, all cover images and test payloads are generated procedurally in memory:
- `ImageGenerator`: Flat colors, smooth gradients, pseudo-natural textures, step wedges, and checkerboards from 64x64 micro covers up to 16 megapixel boundaries ($4000 \times 4000$).
- `PayloadGenerator`: Empty strings, single-byte payloads, complex UTF-8 strings, structured JSON, binary files up to 10 MB, and overflow payloads.
- `TamperGenerator`: Bit-flipping in sequential salt prefixes, ciphertext slots, GCM authentication tags, and image truncation.
