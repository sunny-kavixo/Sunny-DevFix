# Nebius × NVIDIA Global AI Hackathon 2026: Official Compliance Matrix

**Hackathon URL:** [https://nebiusglobalaihackathon.devpost.com/](https://nebiusglobalaihackathon.devpost.com/)  
**Rules Reference:** [https://nebiusglobalaihackathon.devpost.com/rules](https://nebiusglobalaihackathon.devpost.com/rules)  
**Submission Deadline:** October 30, 2026 at 10:00 AM PDT / 10:30 PM IST  
**Judging Period:** November 3 – December 15, 2026  
**Selected Track:** **Coding and Agentic Engineering**  
**Product Title:** Sunny-DevFix — NVIDIA-Powered Verified Code Repair  

---

## 1. Compliance Checklist & Status Overview

| # | Official Devpost Requirement | Compliance Status | Supporting Evidence & Implementation | Risk Level |
| :- | :--- | :---: | :--- | :---: |
| **R1** | **Track Alignment**<br>Must fit *Coding and Agentic Engineering* track. | **PASS** | Sunny-DevFix automates Python traceback debugging, causal reasoning, AI patch synthesis, human-in-the-loop approval, and isolated verification (`agent.py`). | Low |
| **R2** | **Nebius Technology Usage**<br>Must use Nebius Token Factory or Nebius Cloud. | **BLOCKED**<br>(Awaiting live key) | Client implemented at `src/sunny_devfix/providers/nebius.py`. Mocked unit tests verify interface logic only and do NOT satisfy live inference evidence. Live execution pending owner key. | High |
| **R3** | **NVIDIA Open-Source Model**<br>Must use at least one genuine NVIDIA open model. | **BLOCKED**<br>(Awaiting live execution) | Integration code prepared for `nvidia/Nemotron-3_5-Lightning` and `nvidia/Llama-3.1-Nemotron-70B-Instruct`. Mock tests and local AST fallback do NOT satisfy live NVIDIA evidence. Pending authorized run. | High |
| **R4** | **Post-August 26, 2026 Work**<br>Significant new improvements after August 26, 2026. | **PASS** | All repository commits date from October 16, 2026 to October 28, 2026. Explicit pre-existing vs. hackathon work changelog in `docs/hackathon/NEW_WORK_CHANGELOG.md`. | Low |
| **R5** | **Working, Installable App**<br>Clean installation and reproducible tests. | **PASS** | Fully reproducible via `requirements.lock` & `Makefile` with Python 3.14. 80/80 tests pass cleanly in 0.80s. Benchmark latency is 0.18ms. | Low |
| **R6** | **Open Source Repository & License**<br>Public GitHub repo with permissive license. | **PASS** | Permissive MIT License in root `LICENSE`. Clean Git history on branch `feat/nebius-nvidia-verified-repair`. | Low |
| **R7** | **Documentation & Setup Instructions**<br>Clear steps for setup, run, and evaluation. | **PASS** | Comprehensive `README.md`, `DEPLOYMENT_GUIDE.md`, and `JUDGE_TESTING_GUIDE.md` completed. | Low |
| **R8** | **Judge-Accessible Demo / Test Build**<br>Must be testable by judges remotely. | **BLOCKED / PENDING**<br>(Awaiting public release asset) | Local archive `dist/sunny-devfix-v0.2.0.tar.gz` and Docker container are verified locally. A public judge-accessible URL requires owner approval to publish a GitHub Release asset or deploy to Cloud Run. | High |
| **R9** | **Video Submission (< 3 minutes)**<br>Public YouTube video showcasing real features. | **BLOCKED**<br>(Awaiting owner video) | Factual scene-by-scene script & storyboard completed (`DEMO_VIDEO_SCRIPT.md`). Video recording and public YouTube upload requires owner action. | High |
| **R10**| **English Language**<br>All materials in professional English. | **PASS** | All source code, docstrings, UI labels, documentation, and video scripts are in professional English. | Low |
| **R11**| **Technology Feedback**<br>Genuine feedback on Nebius Token Factory & NVIDIA models. | **PASS** | Detailed feedback section prepared in `DEVPOST_SUBMISSION.md` covering latency, structured output support, and agentic reasoning strengths. | Low |
| **R12**| **Third-Party IP & Safety**<br>No copyrighted or unlicensed code. Zero secrets leaked. | **PASS** | 9 adversarial security tests pass in `tests/test_adversarial_security.py`. Strict `.env` isolation; zero server keys in frontend or git; only stdlib/permissive MIT dependencies. | Low |
| **R13**| **Judging Access Maintenance**<br>Available through December 15, 2026. | **PASS** | Serverless Cloud Run ($0/mo) and public GitHub release assets can remain live and accessible through December 15, 2026 without maintenance cost. | Low |

---

## 2. Distinction: Pre-existing vs. Hackathon Additions

To comply with the Devpost requirement of clearly delineating prior work from competition improvements:

### Pre-existing Foundation (Commits Oct 16 – Oct 27, 2026):
1. Deterministic Python traceback parser and frame extractor (`traceback_parser.py`).
2. Pure AST source code analyzer and context extractor (`source_analysis.py`).
3. Live Code Guardian for fast in-browser syntax linting (`guardian.py`).
4. Hardened disposable Docker container runner (`sandbox.py`).
5. Cryptographically tokenized patch preview/apply/rollback subsystem (`patches.py`).

### Significant Hackathon Work (Branch `feat/nebius-nvidia-verified-repair`, Oct 28, 2026):
1. **Nebius Token Factory Client (`src/sunny_devfix/providers/nebius.py`)**:
   - Zero-overhead HTTP client using `httpx` connecting to `https://api.tokenfactory.nebius.com/v1/`.
   - Bounded context window, exponential retry backoff, timeout protection, and automated secret redaction.
   - Clean offline fallback to deterministic AST engine when API key is unset or disabled.
2. **NVIDIA Nemotron Reasoning Provider (`src/sunny_devfix/providers/nvidia_repair.py`)**:
   - Tailored system prompts leveraging NVIDIA Nemotron's advanced reasoning capabilities for root-cause diagnosis.
   - Strict Pydantic JSON schema output enforcing precise unified diffs, root cause explanations, and confidence metrics.
3. **Agentic Code-Repair Orchestrator (`src/sunny_devfix/agent.py`)**:
   - Multi-phase state machine: `ANALYZED` -> `PATCH_PROPOSED` -> `AWAITING_APPROVAL` -> `APPLIED` -> `TESTING` -> `VERIFIED` -> `FAILED` / `ROLLED_BACK`.
   - Bounded retry loop (at most 1 retry if verification fails).
   - Strict approval barrier: AI suggestions *never* auto-execute or overwrite files without human token confirmation.
4. **Professional UI Redesign**:
   - Real-time agent state timeline and execution indicator.
   - Active model badge (NVIDIA Nemotron via Nebius vs. Offline Local Guardian).
   - Side-by-side diff viewer with interactive patch approval and instant rollback controls.
   - Evidence scorecard reflecting Docker container verification.
5. **Comprehensive Submission Suite**:
   - Full test report covering unit, integration, and security adversarial tests (`docs/hackathon/TEST_REPORT.md`).
   - Judge testing guide and complete Devpost submission write-up.
