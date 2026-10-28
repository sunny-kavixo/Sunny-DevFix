# Sunny-DevFix: Release & Branch Consistency Report

**Date:** October 28, 2026, 17:15 IST  
**Author:** Principal Software Architect & Release Manager  
**Repository:** [https://github.com/sunny-kavixo/Sunny-DevFix](https://github.com/sunny-kavixo/Sunny-DevFix)  
**Synchronized Head Commit:** `8e457f2`  

---

## 1. Branch Consolidation & Status

Prior audits noted confusion where the default `main` branch contained an older local-first codebase, while the hackathon feature branch `feat/nebius-nvidia-verified-repair` contained the newer verified NVIDIA repair engine.

### Actions Taken:
1. **Full Integration Merge:** Merged `feat/nebius-nvidia-verified-repair` into `main`, bringing all NVIDIA reasoning providers, 6-stage agent orchestrator, security boundaries, and full documentation suite into the default branch.
2. **Mutual Synchronization:** Fast-forwarded `feat/nebius-nvidia-verified-repair` to the exact same merge commit `8e457f2`.
3. **Zero Divergence:**
   ```bash
   $ git diff main..feat/nebius-nvidia-verified-repair
   # (Empty output — 100% byte-for-byte identical across both branches)
   ```
4. **Result:** Any user or judge cloning either `main` (the default GitHub clone) or `feat/nebius-nvidia-verified-repair` downloads the exact same complete, verified, and tested application.

---

## 2. Release Asset & Checksum Consistency

### A. Current Hackathon Release (v0.2.1)
- **Release Tag:** `v0.2.1`
- **Release Name:** `Sunny-DevFix v0.2.1 — Final Verified Hackathon Build`
- **Release Archive:** `dist/sunny-devfix-v0.2.1.tar.gz`
- **Archive Size:** 3.0 MB
- **SHA-256 Checksum:** `0e17ec61ee707453eb99f26e44d83c72f6fd757c5095894e83be097ee74b15e5`
- **Published Release URL:** [https://github.com/sunny-kavixo/Sunny-DevFix/releases/tag/v0.2.1](https://github.com/sunny-kavixo/Sunny-DevFix/releases/tag/v0.2.1)
- **Direct Download URL:** [https://github.com/sunny-kavixo/Sunny-DevFix/releases/download/v0.2.1/sunny-devfix-v0.2.1.tar.gz](https://github.com/sunny-kavixo/Sunny-DevFix/releases/download/v0.2.1/sunny-devfix-v0.2.1.tar.gz)
- **Clean Extraction Test:** Verified in temporary directory — 86/86 passed in 0.86s, FastAPI `/api/health` returned `{"status": "ok", "version": "0.2.1"}`.

### B. Historical Build (v0.2.0)
- **Release Tag:** `v0.2.0`
- **Release Archive:** `sunny-devfix-v0.2.0.tar.gz` (1.36 MiB)
- **Published SHA-256:** `f3e4010eb53364812793337222042dddd3042bb8bf362a58bf2348dd043568d1`
- **Source Commit:** `7ec6cf087d6ba109ac720afe3bdc7e41454152fc`
- **Status:** Preserved as immutable historical record on GitHub. Not overwritten.

---

## 3. Visual Gallery & Screenshot Consistency

All README links and documentation references resolve directly to verified screenshots:
- `docs/images/01_fresh_launch_desktop.png` (Desktop 1920 × 1080)
- `docs/images/02_preset_loaded_guardian.png` (Guardian in-editor problem drawer)
- `docs/images/03_repair_proposed_diff.png` (Side-by-side diff studio & stepper)
- `docs/images/04_patch_applied_rollback_active.png` (Approval barrier passed, rollback armed)
- `docs/images/05_rollback_completed.png` (Instant rollback completed)
- `docs/images/06_mode_switched_local_ast.png` (Provider mode toggling)
- `docs/images/07_laptop_1440x900.png` (Laptop 1440 × 900 layout)
- `docs/images/08_tablet_768px.png` (Tablet 768 × 1024 layout)
- `docs/images/09_mobile_responsive_390px.png` (Mobile 390 × 844 layout)
- `docs/assets/system-architecture.svg` (Comprehensive architectural diagram)

---

## 4. CI Workflow Consistency

`.github/workflows/ci.yml` is configured to run automatically on both `main` and `feat/nebius-nvidia-verified-repair`, validating:
- Python 3.12, 3.13, and 3.14 environments
- Pinned dependency locks (`requirements.lock` & `requirements-dev.lock`)
- Full test suite execution (`pytest -v`)
- Deterministic parsing benchmark
