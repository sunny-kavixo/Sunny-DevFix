# Sunny DevFix capability assessment

This document keeps advertised capabilities aligned with verified behavior for
the Frontier Buildathon 2026 submission.

## Shipped and verified

| Capability | Current evidence |
| --- | --- |
| Live Code Guardian | Debounced browser calls to `/api/guardian`; syntax, undefined-name, and literal division-by-zero diagnostics are line-aware with severity/confidence labels. |
| Conservative repair | Name spelling and unambiguous missing-colon fixes are proposed only when the source comparison and syntax validation support them. |
| User approval | Browser and VS Code flows apply fixes only after an explicit click or Quick Fix action. |
| Before/after comparison | The API and browser show original source, proposed source, and a copyable unified diff. |
| Evidence-driven repair | `/api/evidence` can run before/after versions in separate hardened Docker containers when explicitly enabled and confirmed. |
| Safety boundary | Static analysis never imports or executes submitted source. Evidence execution is never direct host execution. |
| VS Code integration | Dependency-free extension prototype publishes Problems diagnostics and user-approved Quick Fix actions to a local engine. |
| Chrome integration | Clearly labeled, narrow Manifest V3 prototype for localhost textareas and Monaco input areas; local-only permissions and explicit apply action. |
| Causal debugging | Traceback frames, deepest-frame mapping, root-cause explanation, confidence, and fix limitation are shown in the API/UI. |

## Explicit limitations

### Functional evidence

Evidence is a reproducible result for one source/input pair, not a proof of
general correctness. The UI labels this as a reproduction claim and reports
timeouts, exit codes, output, and regressions separately.

### VS Code

The extension is contract-tested and JavaScript-syntax checked. A VS Code
Extension Development Host is not installed in the offline project image, so a
real VS Code UI run remains a manual demonstration step.

### Chrome extension

The Chrome artifact is a prototype, not a universal integration. It supports
only localhost pages with a discoverable textarea/Monaco input area. Hosted
IDEs, cross-origin iframes, and editors with incompatible controlled-input
implementations are outside the tested scope.

### Advanced capabilities

Cross-file dependency analysis, predictive risk scoring, persistent debugging
history, rollback storage, and benchmark dashboards remain unshipped. The
current scope favors a verified local workflow over placeholder controls.
