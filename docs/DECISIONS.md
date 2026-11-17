# StegaShield — Architecture & Design Decisions Log

This document records key technical, cryptographic, and architectural choices, alternatives considered, and tradeoffs made during development.

---

## ADR-01: FastAPI Backend with Pure Python Core

- **Decision**: Build the backend using Python 3.12+ and FastAPI, strictly isolating `backend/app/core/` from web frameworks and databases.
- **Alternatives Considered**: Node.js / Express, Flask, Django.
- **Rationale**: Python provides the industry standard ecosystem for numerical computing, matrix manipulation, and image processing (`numpy`, `scipy`, `pillow`). FastAPI provides asynchronous high-performance routing, automatic OpenAPI specification generation, and Pydantic v2 data validation.
- **Tradeoff**: Two primary languages in the codebase (Python and TypeScript), managed through strong OpenAPI type contracts.

---

## ADR-02: Next.js 15 App Router with Typed Client

- **Decision**: Develop the frontend with Next.js 15 (App Router), Tailwind CSS, and a generated typed client via `openapi-typescript` + `openapi-fetch`.
- **Alternatives Considered**: Streamlit, plain React Single Page Application (Vite).
- **Rationale**: Next.js App Router delivers professional UI architecture, server-rendered static layout optimization, clean routing, and accessibility. Generating typed clients directly from the backend's `openapi.json` guarantees end-to-end type safety with zero manual duplication of API contracts.
- **Tradeoff**: Slightly higher initial scaffolding effort compared to low-code tools like Streamlit, but yields a production-grade, highly polished UI suitable for rigorous academic evaluation.

---

## ADR-03: MySQL 8 with PyMySQL and SQLAlchemy 2.x

- **Decision**: Use MySQL 8 as the primary relational database with SQLAlchemy 2.0 ORM and Alembic migrations.
- **Alternatives Considered**: PostgreSQL, MongoDB, SQLite exclusively.
- **Rationale**: MySQL 8 is standard, robust, and already available on the development machine. SQLAlchemy 2.0 provides database independence with parameterized SQL queries preventing injection, while Alembic enables repeatable, version-controlled schema migrations.
- **Tradeoff**: In-memory SQLite is used during automated unit/integration test runs (`tests/api/`) for rapid hermetic testing, with full MySQL compatibility maintained across column types and timestamps.

---

## ADR-04: Cryptographic Primitives (scrypt + HKDF-SHA256 + AES-256-GCM)

- **Decision**: Derive keys using scrypt ($N=131072, r=8, p=1$), separate duties via HKDF-SHA256, and encrypt using AES-256-GCM with ciphertext length bound into AAD.
- **Alternatives Considered**: PBKDF2-HMAC-SHA256, Argon2id, AES-CBC with HMAC.
- **Rationale**: scrypt is widely standardized (RFC 7914) and memory-hard (~128 MiB RAM per derivation), protecting low-entropy passwords against GPU/ASIC parallel brute-force attacks. HKDF ensures independent encryption and permutation keys. AES-GCM provides AEAD (Authenticated Encryption with Associated Data) preventing ciphertext tampering.
- **Tradeoff**: High scrypt memory requirement (~128 MiB per call); tests use configured lower parameters where appropriate while production defaults strictly maintain $N=2^{17}$.

---

## ADR-05: Non-Adaptive Embedding (LSB Replacement vs. LSB Matching)

- **Decision**: Implement both LSB replacement and LSB matching ($\pm 1$ embedding) with PRNG spatial dispersion.
- **Alternatives Considered**: Content-adaptive steganography (HUGO, S-UNIWARD, WOW).
- **Rationale**: Non-adaptive LSB methods perfectly illustrate the core academic concepts of information hiding and statistical detection. Implementing both allows direct side-by-side comparison in the Attack Lab, demonstrating why LSB matching defeats Chi-Square attacks while LSB replacement succumbs to it. Content-adaptive methods require complex distortion cost functions and are documented as future research work.

---

## ADR-06: Classical Statistical Steganalysis (Chi-Square & RS Analysis)

- **Decision**: Implement Westfeld & Pfitzmann (2000) Chi-Square attack and Fridrich et al. (2001) Regular/Singular (RS) analysis with fully vectorized NumPy implementations.
- **Alternatives Considered**: Deep learning CNN steganalysis (SRNet, Xu-Net), SPAM features.
- **Rationale**: Classical detectors are deterministic, explainable, and run in milliseconds on standard CPUs without GPU dependencies. They clearly demonstrate the exact mathematical vulnerabilities of LSB replacement (Pairs of Values equalization).

---

## ADR-07: Anonymous Session Cookie for History and Rate Limiting

- **Decision**: Use anonymous random UUID session cookies (`HttpOnly`, `SameSite=Lax`) to scope history and rate limits without user registration.
- **Alternatives Considered**: Full OAuth/JWT authentication, global shared history.
- **Rationale**: Aligns strictly with non-goals (no user accounts/passwords) while ensuring privacy and preventing collision of operations during interactive student evaluations.
