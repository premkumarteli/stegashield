# StegaShield — Master Specification v1.0

**Audience:** AI coding agent (Antigravity) acting as lead engineer.
**Owner:** Prem, final-year ISE student. **Context:** academic project for the subject *Information and Network Security*. **Deadline:** about 1 day of work.
**Product in one line:** a steganography and steganalysis lab. It hides encrypted data in images, then attacks its own images with real statistical detectors and shows the results in a polished web UI.

---

## 0. How you must work (read first)

You are the lead engineer. The owner reviews your work at the end of every phase. These rules are mandatory.

- **R-1 Phase discipline.** Work on ONE phase at a time. When a phase is done, STOP and post a PHASE REPORT (format in section 14). Do not start the next phase until the owner writes "GO PHASE N".
- **R-2 Honest reporting.** Never fabricate test results, benchmark numbers or detection rates. Show real command output. If something fails or is only partly working, say so plainly. Never tune a threshold, test or detector just to make a test pass.
- **R-3 No invented science.** Implement the algorithms from the cited papers. Do not invent formulas. Do not add fake citations.
- **R-4 No scope creep.** The non-goals in section 1 are binding. If you think something extra is needed, propose it in `docs/DECISIONS.md` and ask. Do not silently add it.
- **R-5 Real data only.** The UI must never show placeholder or made-up numbers. Charts and tables show only measured results from the database. No lorem ipsum.
- **R-6 Secrets.** No secrets in code or git. Use `.env` (git-ignored) and commit `.env.example`. Never log passwords, keys, plaintext messages or payload bytes.
- **R-7 Quality bar.** Python 3.12 with type hints, `ruff` and `mypy --strict` on `core/`. TypeScript with `strict: true` and no `any`. Small functions with docstrings. Comments explain WHY, not WHAT.
- **R-8 Dependencies.** Pin versions. Every dependency not listed in section 5 must be justified in `docs/DECISIONS.md`.
- **R-9 Git.** Small commits with clear messages (`feat:`, `fix:`, `test:`, `docs:`). One commit at minimum per phase, tagged `phase-N`.
- **R-10 Explainability.** The owner must defend this project in a viva. Keep the core simple and readable. Prefer clarity over cleverness.
- **R-11 Cross-platform.** The owner may develop on Windows. The README must give both PowerShell and bash commands. Avoid bash-only tooling.
- **R-12 Ambiguity.** If a requirement is ambiguous, choose the most reasonable reading, record it in `docs/DECISIONS.md` under "Assumptions", and continue. Ask only if the choice is expensive to reverse.

---

## 1. Vision, goals, non-goals

**Goals**
- G1. Hide text or small files in PNG images, protected by password-based authenticated encryption.
- G2. Support two embedding methods (LSB replacement, LSB matching) so they can be compared.
- G3. Provide real steganalysis (chi-square and RS analysis) and measure how well they detect each method at different payload sizes.
- G4. Make the security story visible: a clean, modern, professional UI with charts.
- G5. Be reproducible, tested and documented.

**Non-goals (do NOT build)**
- User accounts, login, JWT, OAuth. (Anonymous session cookie only.)
- Redis, Celery, message queues, microservices, WebSockets.
- Deep-learning steganalysis, JPEG/DCT-domain embedding, audio or video steganography.
- Content-adaptive embedding such as HUGO, WOW or S-UNIWARD. (Mention as future work only.)
- Cloud deployment. (Local run only; Docker is optional in Phase 5.)

---

## 2. Technical Stack
- Backend: Python 3.12+, FastAPI, Pydantic v2, pydantic-settings, Uvicorn, NumPy, SciPy, Pillow, scikit-image, cryptography.
- Database: MySQL 8 / SQLite test fallback, SQLAlchemy 2.x, Alembic, PyMySQL.
- Frontend: Next.js 15 App Router, TypeScript (strict), Tailwind CSS, Lucide icons, TanStack Query.
- Styling: Abyssal Liquid Glass design system.
