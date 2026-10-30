# Sunny-DevFix Silent Demo — Voice-over Timeline

**Video:** `Sunny-DevFix-Final-Demo-SILENT.mp4`  
**Target duration:** 2 minutes 50 seconds  
**Format:** 1920 × 1080, H.264, 30 FPS, no audio stream

Use this timeline as a guide for recording your own narration. The video is intentionally silent.

| Time | What appears on screen | Functionality demonstrated | Suggested talking points |
| --- | --- | --- | --- |
| 00:00–00:23 | Sunny-DevFix workspace with a defective Python billing function and its traceback | A real `NameError` example is loaded into the application | “Sunny-DevFix turns a Python traceback into a controlled repair workflow. This example references `tx`, although the function defines `tax`.” |
| 00:23–00:47 | Product workspace, provider controls, status indicators, and safety-oriented layout | Project identity and the distinction between NVIDIA-assisted repair and the deterministic local AST fallback | “The interface states which repair provider is active. Local analysis remains available when cloud inference is not configured; the product does not mislabel deterministic output as AI-generated.” |
| 00:47–01:11 | Multiple genuine bug presets and Live Code Guardian results | Non-executing source analysis and diagnostic reporting | “The guardian inspects source with Python’s AST rather than running untrusted code. Findings are diagnostics, not changes to disk.” |
| 01:11–01:36 | Repair action, causal explanation, lifecycle stepper, and proposed result | `DETECTED`, `PROPOSED`, and `PREVIEWED` states | “The traceback is mapped to the failing line, a minimal repair is proposed, and the workflow stops at `AWAITING_APPROVAL`. A proposal is not yet an applied fix.” |
| 01:36–02:01 | Before/after comparison, unified diff, and human authorization gate | Readable patch preview and explicit approval barrier | “The exact edit is reviewable before any write. Applying to disk requires an authorized project root, a content-bound one-time approval token, and explicit human confirmation.” |
| 02:01–02:22 | Apply/verification evidence followed by Instant Rollback | `APPROVED`, `APPLIED`, verification evidence, and `ROLLED_BACK` states | “The approved patch is written atomically. Verification is shown as a separate state rather than assumed from application, and rollback restores the original bytes with a one-time token.” |
| 02:22–02:40 | Technical evidence and responsive product UI | Automated backend, API, security, and browser validation evidence | “The release is covered by 86 automated tests plus a real Chrome lifecycle check across desktop, laptop, tablet, and mobile viewports.” |
| 02:40–02:50 | Sunny-DevFix identity, repository, and open-source close | Final project identity and submission handoff | “Sunny-DevFix is an MIT-licensed, human-in-the-loop debugging assistant powered by NVIDIA Nemotron through Nebius Token Factory, with a deterministic offline fallback.” |

## Recording notes

- Record narration separately and add it as a new audio track in your editor.
- Keep the original silent MP4 unchanged as a clean submission master.
- Do not describe an in-memory preview as an applied patch or an applied patch as verified until the verification evidence is visible.
- If presenting the cloud path, say that NVIDIA Nemotron is used only when Nebius credentials are configured; otherwise the UI truthfully reports the local deterministic engine.
