# Sunny DevFix 2–3 minute demonstration

Use the local engine and the browser UI. Keep the demo focused on one complete
workflow and show the safety boundary honestly.

## Before recording

```bash
make test
DEVFIX_SANDBOX_ENABLED=true make run
```

The evidence button requires the local service to reach Docker and the
`sunny-devfix:local` image to exist. If that configuration is unavailable,
show the honest “evidence not run” state rather than simulating a pass.

## Suggested sequence

1. **0:00–0:20 — Context**
   Say: “Sunny DevFix is a local-first Python debugging assistant. Source is
   analyzed locally, and no fix is applied without approval.”
2. **0:20–0:55 — Live Guardian**
   Click **Load example**, or type:

   ```python
   def greet(user_name):
       return "Hello, " + username
   ```

   Pause for the debounced undefined-name diagnostic. Point out the line,
   severity, confidence, explanation, and **Review & apply** action.
3. **0:55–1:25 — Approved correction**
   Click **Review & apply**. Show that the editor changes only after the click,
   then show the guardian returning clean diagnostics.
4. **1:25–1:55 — Traceback readout**
   Use the example traceback and click **Analyze traceback**. Show the deepest
   frame, plain-language cause, before/after code, and unified diff.
5. **1:55–2:35 — Evidence Lab**
   Click **Verify in Docker**. Show separate before/after statuses and the
   scorecard. Say: “This verifies this reproduction only; it is not a claim of
   general correctness.”
6. **2:35–3:00 — Developer-tool proof**
   If a VS Code Extension Development Host is available, open the extension
   folder, edit a Python file, and show the Problems panel plus Quick Fix.
   Otherwise show `extensions/sunny-devfix-vscode/README.md` and state that
   the extension is contract-tested but the host was not available in CI.

## Never claim during the demo

- Do not say the app executes code on the host.
- Do not say a syntax pass proves functional correctness.
- Do not claim universal Chrome editor compatibility.
- Do not claim VS Code runtime verification unless the Extension Development
  Host was actually run.
