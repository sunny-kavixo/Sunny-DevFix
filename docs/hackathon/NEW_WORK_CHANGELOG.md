# Sunny-DevFix: Provenance and New Work Changelog

**Hackathon Requirement:** Clear distinction between pre-existing work and significant new work created after August 26, 2026.  
**Track:** Coding and Agentic Engineering  
**Working Feature Branch:** `feat/nebius-nvidia-verified-repair`  
**Baseline Git SHA:** `0e36aaa642eea6e21e3c0d5b5cd8d2f0cb509c82` (Merged 2026-10-27)  

---

## 1. Provenance Breakdown

### Pre-existing Foundation (Baseline Commits: Oct 16 – Oct 27, 2026)
*All work post-dates August 26, 2026.*

| Commit | Date | Author | Description / Scope |
| :--- | :---: | :--- | :--- |
| `3c62e83` | 2026-10-16 | sunny-kavixo | Project foundation, `pyproject.toml`, pinned lockfiles, MIT LICENSE. |
| `b26568b` | 2026-10-16 | sunny-kavixo | Deterministic traceback parser and source line mapping. |
| `04438de` | 2026-10-16 | sunny-kavixo | Initial FastAPI service endpoints and browser workspace shell. |
| `d5b0e21` | 2026-10-16 | sunny-kavixo | Conservative heuristic suggestions and standard unified diff builder. |
| `419ab32` | 2026-10-16 | sunny-kavixo | Live Code Guardian AST linter and Docker evidence runner prototype. |
| `dd50bc5` | 2026-10-16 | sunny-kavixo | Contract tests for VS Code extension prototype. |
| `7b141b3` | 2026-10-16 | sunny-kavixo | Scoped Chrome extension prototype manifest. |
| `c185552` | 2026-10-27 | sunny-kavixo | Cryptographic patch preview/apply/rollback security subsystem. |
| `e5c6c81` | 2026-10-27 | sunny-kavixo | Token lifecycle unit tests and file permission preservation. |
| `0e36aaa` | 2026-10-27 | sunny-kavixo | Clean baseline merge of `feat/devfix-advanced-product-v2` into `main`. |

---

## 2. Significant Hackathon Work (Branch `feat/nebius-nvidia-verified-repair`, Oct 28, 2026)

The following capabilities were engineered specifically for the **Nebius × NVIDIA Global AI Hackathon 2026**:

### A. Nebius Token Factory Integration (`src/sunny_devfix/providers/nebius.py`)
- Engineered a zero-overhead HTTP client connecting directly to `https://api.tokenfactory.nebius.com/v1/chat/completions`.
- Integrated strict timeout controls (default 20.0s), character payload bounds (30,000 characters), and exponential retry backoff on HTTP 429 and 5xx errors.
- Built automatic secret redaction (`[REDACTED]`) for diagnostic status endpoints and logs to prevent credential leakage.
- Added comprehensive unit tests (`tests/test_nebius_client.py`).

### B. NVIDIA Nemotron Reasoning Provider (`src/sunny_devfix/providers/nvidia_repair.py`)
- Selected and integrated the verified runtime model `nvidia/Nemotron-3_5-Lightning`.
- Designed specialized system prompts and strict Pydantic JSON schemas (`NvidiaRepairOutput`) enforcing structured root-cause explanations, actionable advice, and surgical patch proposals.
- Implemented AST-level compilation verification of all model-proposed code before acceptance.
- Built automated, graceful fallback to the trusted local deterministic AST analyzer whenever Nebius credentials are absent or network is offline.

### C. Autonomous Agentic Code-Repair Orchestrator (`src/sunny_devfix/agent.py`)
- Implemented complete agent lifecycle state machine:
  `IDLE` → `ANALYZED` → `PATCH_PROPOSED` → `AWAITING_APPROVAL` → `APPLIED` → `TESTING` → `VERIFIED` (or `ROLLED_BACK`).
- Enforced human-in-the-loop approval gates: AI-generated code is never applied without a cryptographically bound approval token and explicit user confirmation.
- Integrated optional Docker container execution with verification scorecards (syntax check, reproduction pass/fail, and regression detection).
- Implemented single-use rollback mechanics with filesystem integrity verification.

### D. New API Endpoints & Extended Schemas (`src/sunny_devfix/api/routes.py`, `schemas.py`)
- `GET /api/model-info`: Returns non-sensitive runtime diagnostics, model ID, provider name, and key status.
- `POST /api/agent/repair`: Executes end-to-end agentic repair cycle.
- `POST /api/agent/apply`: Confirms and executes tokenized patch application.
- `POST /api/agent/rollback`: Restores pre-patch file state.

### E. Professional UI/UX Upgrade (`static/index.html`, `style.css`, `app.js`)
- Dynamic agent lifecycle visualizer with real-time state pulse indicator and timeline log.
- Live model provider badge reflecting Nebius/NVIDIA status vs. offline fallback mode.
- Side-by-side Before/After preview with colored unified diffs (additions in green, deletions in red).
- Example bug library containing 4 realistic Python defect scenarios (NameError, SyntaxError, ZeroDivisionError, IndexError).
- Interactive patch approval dialog and instant one-click rollback controls.

### F. Adversarial & Security Test Suite (`tests/test_adversarial_security.py`)
- 9 dedicated security tests verifying prompt injection resistance, path traversal rejection, symlink escape protection, replay attack prevention, and secret masking.
- Increased the total test suite from 50 to 81 tests (100% pass rate in the final local run).
