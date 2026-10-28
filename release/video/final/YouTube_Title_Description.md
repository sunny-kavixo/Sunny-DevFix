# YouTube Title & Description — Sunny-DevFix Final Release

## Title
```
Sunny-DevFix — NVIDIA-Powered Verified Code Repair (Nebius × NVIDIA Hackathon 2026)
```

## Description
```markdown
Sunny-DevFix: Autonomous Causal Python Debugging & Verified Code Repair Engine.
Submitted to the Nebius × NVIDIA Global AI Hackathon 2026 under the "Coding and Agentic Engineering" track.

Sunny-DevFix solves one of the most critical hazards in agentic coding: unconstrained AI agents that hallucinate non-existent APIs and introduce breaking regressions. By coupling NVIDIA Nemotron open-source reasoning models on Nebius Token Factory with local deterministic AST guardrails, a cryptographic human approval barrier, and isolated container verification, Sunny-DevFix turns raw Python tracebacks into verified, bounded repairs.

✦ Key Technical Capabilities:
- NVIDIA Nemotron Reasoning: Cloud model inference via Nebius Token Factory for complex multi-frame root cause analysis.
- Offline Deterministic AST Engine: Local rule-based repair engine capable of zero-cloud offline repairs in 0.18ms.
- Live Code Guardian: Real-time non-executing AST syntax diagnostics as you type.
- Cryptographic Approval Gate: One-time token required before writing to authorized workspace files. Zero autonomous code modifications.
- Isolated Docker Verification: Reproduction runs with --network none, read-only root filesystem, and strict memory limits.
- Instant One-Click Rollback: Cryptographically bound rollback token restores pre-patch state in milliseconds.

Chapters & Video Timeline:
0:00 — Problem Statement: The Hazard of Naive Agentic Coding
0:23 — Product Introduction: Modern 3-Column AI Developer Workspace
0:47 — Live Debugging Intake: Raw Traceback & Live Code Guardian
1:11 — Agent Reasoning: NVIDIA Nemotron on Nebius Token Factory
1:36 — Patch Inspection: Unified Diff & Cryptographic Approval Gate
2:01 — Verification & Rollback: Isolated Docker Container & Instant Recovery
2:22 — Technical Evidence: 80 Passing Tests & 0.18ms Benchmark Latency
2:40 — Conclusion: Open Source MIT License & Evaluation Links

Repository: https://github.com/sunny-kavixo/Sunny-DevFix
Branch: feat/nebius-nvidia-verified-repair
License: MIT License
Evaluator Test Archive: dist/sunny-devfix-v0.2.0.tar.gz (SHA256 verified)
```
