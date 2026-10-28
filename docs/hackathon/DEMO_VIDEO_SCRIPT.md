# Sunny-DevFix: Demonstration Video Storyboard & Script

**Event:** Nebius × NVIDIA Global AI Hackathon 2026  
**Track:** Coding and Agentic Engineering  
**Target Duration:** 2 minutes 55 seconds (strictly under 3 minutes)  
**Host Platform:** Public YouTube Video  
**Language:** English  

---

## 1. Scene-by-Scene Storyboard & Narration Script

### Scene 1: The Problem & Product Overview (0:00 – 0:20)
- **Visual**: Screen capture showing terminal filled with a complex, intimidating Python traceback (e.g. `billing.py` NameError/KeyError), then cutting to the sleek Sunny-DevFix browser interface at `http://127.0.0.1:8000`.
- **Narration**:
  > "Every developer knows the pain of staring at a multi-frame Python traceback, guessing the root cause, and hoping a chatbot's suggestion doesn't silently break production code. 
  > This is **Sunny-DevFix** — an agentic code repair assistant powered by **NVIDIA Nemotron** on **Nebius Token Factory** that diagnoses defects, synthesizes surgical patches, and verifies them in isolated containers before anything touches disk."

### Scene 2: The Agentic Workflow & Input Workspace (0:20 – 0:45)
- **Visual**: Demonstrating the Example dropdown (`Example 1: NameError`), clicking **Load**, and showing the immediate response of the **Live Code Guardian** AST linter highlighting the error on line 3.
- **Narration**:
  > "In the workspace, we paste defective source code and the runtime traceback. 
  > Notice our Live Code Guardian: as you type, it continuously parses AST structures locally without executing untrusted code or making cloud calls. It pinpoints the defect and explains the issue immediately."

### Scene 3: NVIDIA Nemotron on Nebius Token Factory (0:45 – 1:15)
- **Visual**: Clicking **AI Repair (NVIDIA) ✦**. The top-right badge displays `● NVIDIA Nemotron · Nebius Token Factory`. The **Agent Workflow Lifecycle** stepper pulses as it moves from `ANALYZED` to `PATCH PROPOSED`.
- **Narration**:
  > "Now, we trigger the agentic repair. The engine sends bounded context to `nvidia/Llama-3.1-Nemotron-70B-Instruct` hosted serverless on **Nebius Token Factory**. 
  > Nemotron analyzes the call stack, evaluates Python scoping rules, and returns a strictly typed JSON structure containing the causal explanation and a minimal, verified repair."

### Scene 4: Patch Synthesis, Side-by-Side Diff & Human Approval (1:15 – 1:50)
- **Visual**: The UI displays the plain-language root cause explanation and reveals the side-by-side **Before vs After** code viewer and the colored **Unified Diff** (with green additions and red deletions). Hovering over **Approve & Apply (Disk)**.
- **Narration**:
  > "Nemotron identifies that `tx` was referenced instead of parameter `tax`. 
  > Before anything is applied, Sunny-DevFix enforces a strict human-in-the-loop barrier. 
  > We inspect the before-and-after source and a clear unified diff. 
  > An approval token bound to the exact file SHA-256 is generated. Clicking 'Approve & Apply' atomically updates the file and issues a one-time cryptographic rollback token."

### Scene 5: Isolated Docker Sandbox Verification & Rollback (1:50 – 2:20)
- **Visual**: Clicking **Verify in Docker**. The Evidence Lab panel updates to show before (failed, exit 1) vs after (passed, exit 0) runs in disposable containers. Then demonstrating the **Instant Rollback** button restoring pre-patch bytes.
- **Narration**:
  > "To guarantee correctness, we run reproduction evidence in disposable Docker containers. 
  > Under strict zero-trust constraints — no network, read-only root, and a 128-megabyte cap — both versions run in isolation. 
  > The scorecard confirms the fix passed with zero regression. And if an unexpected edge case is observed, a single click on 'Instant Rollback' immediately restores the exact pre-patch code."

### Scene 6: Architecture & Measurable Value (2:20 – 2:45)
- **Visual**: Fast overview of the architecture diagram and the test execution in terminal (`80 passed in 0.80s`, benchmark latency `0.18ms`).
- **Narration**:
  > "Under the hood, Sunny-DevFix is backed by 80 comprehensive tests — including adversarial security suites for prompt injection and path traversal. 
  > With median local latency under 0.2 milliseconds, it seamlessly falls back to a deterministic local engine if offline, ensuring your development workflow is never blocked."

### Scene 7: Wrap-up & Call to Action (2:45 – 2:55)
- **Visual**: Final screen displaying the GitHub repository link, MIT License badge, and track alignment.
- **Narration**:
  > "Sunny-DevFix brings accountability, safety, and verifiable evidence to agentic AI engineering. 
  > Explore the open-source repository on GitHub and test it today. Thank you!"

---

## 2. Recording & Production Checklist

1. **Resolution**: 1920x1080 (1080p 60fps).
2. **Audio**: Clean, noise-free English voiceover.
3. **Pacing**: Steady speech cadence (~140 words per minute).
4. **Time Verification**: Video duration MUST measure between 2:45 and 2:58.
5. **Approval**: Owner must approve before public YouTube upload.
