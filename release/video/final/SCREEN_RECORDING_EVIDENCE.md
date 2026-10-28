# Screen Recording Evidence & Frame Capture Log

**Deliverable Directory:** `release/video/final/clips/`  
**Capture Engine:** Headless Google Chrome over DevTools Protocol (CDP)  
**Viewport Resolution:** 1920 × 1080 (Full HD, 16:9)  
**Frame Rate:** 12 fps native capture, 30 fps compiled output  

---

## 1. Recorded Application Clips

| Clip Filename | Duration | Frame Count | Captured Application Interactions |
| :--- | :---: | :---: | :--- |
| `scene1_problem.mp4` | 23.0s | 276 | Live defective source input, raw traceback parsing, input focus on billing calculation bug |
| `scene2_product_intro.mp4` | 24.0s | 288 | 3-column AI workspace overview, switching inference modes (NVIDIA Nemotron vs Local AST), header status chips |
| `scene3_live_debugging.mp4` | 24.0s | 288 | Bug preset switching (SyntaxError, ZeroDivisionError, NameError), Live Code Guardian AST diagnostics strip |
| `scene4_agent_reasoning.mp4` | 25.0s | 300 | Triggering AI Repair, pulsing agent stepper progression (01 -> 02 -> 03), causal root-cause explanation |
| `scene5_patch_diff.mp4` | 25.0s | 300 | Side-by-side comparison, syntax-highlighted Unified Diff, copy buttons, human approval barrier |
| `scene6_verification_rollback.mp4` | 21.0s | 252 | Docker container execution trigger, execution scorecard, instant rollback restoring pre-patch source |
| `scene7_technical_evidence.mp4` | 18.0s | 216 | Terminal test runner showing 80 passing tests, benchmark metrics (0.18ms latency) |
| `scene8_conclusion.mp4` | 10.0s | 120 | Application topbar, open-source MIT license, GitHub repository showcase |

**Total Cumulative Footage:** 170.0 seconds (2,040 individual Full HD frames)

---

## 2. Screenshot Evidence Gallery

Captured high-resolution Full HD screenshots saved in `release/screenshots/final_ui/`:
1. `01_fresh_launch_desktop.png` — Clean launch of redesigned 3-column AI developer workspace.
2. `02_preset_loaded_guardian.png` — Preset loaded with Live Code Guardian AST diagnostic active.
3. `03_repair_proposed_diff.png` — Synthesized repair with side-by-side Before/After diff and color-coded unified diff.
4. `04_patch_applied_rollback_active.png` — Patch approved and applied to authorized target; one-click rollback token active.
5. `05_rollback_completed.png` — Successful instant rollback restoring exact pre-patch code.
6. `06_mode_switched_local_ast.png` — Active inference mode switched to Local Deterministic AST Engine.
7. `07_mobile_responsive_390px.png` — Clean single-column mobile viewport (iPhone 14, 390px width) without horizontal overflow.
