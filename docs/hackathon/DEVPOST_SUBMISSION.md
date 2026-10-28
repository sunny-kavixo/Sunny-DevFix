# Devpost Submission: Sunny-DevFix — NVIDIA-Powered Verified Code Repair

**Event:** Nebius × NVIDIA Global AI Hackathon 2026  
**Track:** Coding and Agentic Engineering  
**Submission Title:** Sunny-DevFix — NVIDIA-Powered Verified Code Repair  
**Tagline:** Autonomous Python traceback debugging and verified patch repair powered by NVIDIA Nemotron on Nebius Token Factory with human-in-the-loop safety and isolated Docker verification.  

---

## 1. The Problem & Target Audience

Every software developer loses hours deciphering obtuse runtime stack traces, finding the root cause across call frames, formulating a tentative fix, and testing whether the fix actually works or introduces silent regressions. 

While general-purpose LLM chatbots can propose code snippets, they present acute hazards in professional engineering environments:
1. **Hallucinated or Breaking Patches**: LLMs often generate plausible-looking code that fails syntax compilation or breaks adjacent functions.
2. **Lack of Provenance and Containment**: Direct code execution or silent file modifications risk data loss, symlink escapes, or path traversal.
3. **No Verification Evidence**: Chatbots cannot prove whether a bug was truly resolved.

**Target Audience:** Python backend developers, DevOps engineers, site reliability engineers (SREs), and automated CI/CD triage workflows.

---

## 2. The Solution: Sunny-DevFix

Sunny-DevFix transforms Python runtime debugging into an accountable, verified agentic workflow. By combining **NVIDIA Nemotron's high-capacity causal reasoning on Nebius Token Factory** with deterministic AST analysis, token-bound human approval gates, and disposable Docker container sandboxes, Sunny-DevFix diagnoses the defect, generates a minimal surgical repair, displays an interactive unified diff, and verifies the fix before applying it to disk.

---

## 3. How It Works (The 6-Stage Agent Lifecycle)

Sunny-DevFix implements an explicit state machine:
1. **`ANALYZED`**: When a traceback and source file are submitted, the local AST engine parses the stack trace, extracts chained frames, and maps the deepest failing frame to the exact line and scope in the source code without importing or running untrusted code.
2. **`PATCH_PROPOSED`**: Bounded context is transmitted to `nvidia/Nemotron-3_5-Lightning` via Nebius Token Factory. The model diagnoses the root cause and synthesizes a structured repair conforming to a strict Pydantic JSON schema.
3. **`AWAITING_APPROVAL`**: The engine validates that the proposed code compiles syntactically and generates a side-by-side colored unified diff. If an authorized project root is configured, a 5-minute cryptographic approval token is issued.
4. **`APPLIED`**: The human operator must explicitly click **Approve & Apply**. The patch is written atomically to disk and immediately backed by a single-use rollback token.
5. **`TESTING`**: The engine optionally launches twin disposable Docker containers (`--network none`, `--read-only`, 128MB RAM limit) to execute the before and after reproductions side-by-side.
6. **`VERIFIED` / `ROLLED_BACK`**: The scorecard reports syntax validity, reproduction success, and regression detection. If an unintended side effect is found, clicking **Instant Rollback** immediately restores the original pre-patch bytes.

---

## 4. Technical Architecture & Technology Stack

- **Core Backend**: FastAPI, Pydantic v2, Python 3.14 AST standard library.
- **Model Inference**: Nebius Token Factory (Serverless OpenAI-Compatible API) hosting `nvidia/Nemotron-3_5-Lightning`.
- **Offline Fallback Engine**: Local AST & SequenceMatcher analyzer (100% functional even when offline or unconfigured).
- **Execution Sandbox**: Docker CLI integration enforcing non-root UID `65532:65532`, dropped Linux capabilities, and read-only filesystems.
- **Frontend Workspace**: Zero-framework Vanilla HTML5/CSS3/JavaScript devtool UI featuring an interactive agent lifecycle visualizer, live model indicator, and debounced Live Code Guardian linter.

---

## 5. NVIDIA & Nebius Integration Details

### Nebius Token Factory
- Connects directly to `https://api.tokenfactory.nebius.com/v1/chat/completions`.
- Zero client-side API key leakage: credentials remain strictly in the server environment (`NEBIUS_API_KEY`) and are masked in all diagnostic outputs (`v1.C...s0AL`).
- Includes payload character caps (30,000 chars), request timeouts (20s), and exponential backoff retry logic.

### NVIDIA Model Usage
- Primary Model: `nvidia/Nemotron-3_5-Lightning`.
- Verified Runtime Model: `nvidia/Nemotron-3_5-Lightning`.
- Why NVIDIA Nemotron: NVIDIA Nemotron excels at complex reasoning, code comprehension, and instruction-following. It reliably adheres to structured JSON schemas and understands subtle Python scoping quirks (e.g. variable typos vs. global/local scope shadowing).

---

## 6. Significant New Work Created During Hackathon

Sunny-DevFix separates preexisting foundations from hackathon additions:

### Pre-existing Foundation (Commits Oct 16 – Oct 27, 2026):
- Baseline AST traceback parser (`traceback_parser.py`).
- Live Code Guardian prototype (`guardian.py`).
- Initial container execution harness (`sandbox.py`).
- Baseline token patch manager (`patches.py`).

### Hackathon Additions (Branch `feat/nebius-nvidia-verified-repair`, Oct 28, 2026):
1. **Nebius Token Factory Client (`src/sunny_devfix/providers/nebius.py`)**: Full HTTP client with retries, timeouts, and key redaction.
2. **NVIDIA Nemotron Reasoning Provider (`src/sunny_devfix/providers/nvidia_repair.py`)**: Structured Pydantic schema generation, AST compilation check, and fallback.
3. **Agentic Code-Repair Orchestrator (`src/sunny_devfix/agent.py`)**: Multi-phase state machine, human approval barrier, and rollback verification.
4. **Interactive DevTool UI Upgrade (`static/index.html`, `style.css`, `app.js`)**: Real-time agent state stepper, live model indicator, colored diff viewer, and 4 built-in bug fixtures.
5. **Adversarial & Security Test Suite (`tests/test_adversarial_security.py`)**: 9 new security tests covering prompt injection, path traversal, symlink escapes, and replay attacks.
6. **Total Test Growth**: Expanded from 50 to 80 passing tests (100% pass rate).

---

## 7. Testing & Verification Evidence

```bash
$ python3 -m pytest
============================== 81 passed in 0.80s ==============================

$ PYTHONPATH=src python3 tools/benchmark.py --iterations 2000
{"iterations": 2000, "median_ms": 0.1856, "p95_ms": 0.1894, "peak_traced_kib": 94.9}
```

- **Pass A (Core Baseline)**: 50 tests covering AST parsing, traceback frames, and token lifecycle.
- **Pass B (Functional & Agent)**: 21 tests covering Nebius client, NVIDIA repair provider, agent states, and new API routes.
- **Pass C (Security & Adversarial)**: 9 tests verifying prompt injection defense, path containment, and secret masking.

---

## 8. Honest Technology Feedback

### Feedback on Nebius Token Factory:
- **Strengths**: The OpenAI-compatible API format allowed seamless integration without heavy proprietary SDKs. Response streaming and low time-to-first-token (TTFT) are impressive.
- **Opportunities for Improvement**: Native JSON-schema output enforcement (like OpenAI's `response_format: {"type": "json_schema"}`) would eliminate the need for manual markdown fence stripping and client-side Pydantic retries.

### Feedback on NVIDIA Nemotron:
- **Strengths**: `nvidia/Nemotron-3_5-Lightning` returned a concise, schema-valid diagnosis and surgical Python repair for the recorded synthetic traceback case.
- **Opportunities for Improvement**: Context windows are generous, but guidance on token-efficient prompt templates for automated coding agents would assist builders in minimizing latency.

---

## 9. Submission Metadata & Verification Status

- **Track**: Coding and Agentic Engineering
- **GitHub Repository**: [https://github.com/sunny-kavixo/Sunny-DevFix](https://github.com/sunny-kavixo/Sunny-DevFix)
- **Branch**: `feat/nebius-nvidia-verified-repair`
- **License**: MIT Permissive Open Source
- **Local Verification Status**: **100% PASS** (81/81 unit, functional, and adversarial security tests passing cleanly in 0.79s).
- **Live Nebius & NVIDIA Inference**: **100% PASS** (Live authenticated inference verified on Nebius Token Factory with `nvidia/Nemotron-3_5-Lightning`, returning valid Python syntax in 7.506s with live evidence saved in `docs/hackathon/LIVE_INFERENCE_RECORD.json`).
- **Judge Access**: Public standalone test build and checksum: [Sunny-DevFix v0.2.0](https://github.com/sunny-kavixo/Sunny-DevFix/releases/tag/v0.2.0). Docker and offline local modes are also documented.
- **Demo Video**: Public YouTube link pending owner upload.
