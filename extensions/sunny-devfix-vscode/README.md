# Sunny DevFix VS Code Extension

This small dependency-free extension connects a Python editor to a local Sunny
DevFix engine.

## What it does

- Debounces Python document changes and posts source to `POST /api/guardian`.
- Shows line-level errors and warnings in the VS Code Problems panel.
- Exposes conservative fixes as normal, user-approved VS Code Quick Fix code
  actions.
- Clears diagnostics when the local engine is unavailable instead of making
  claims from stale data.

## Try it locally

1. Start Sunny DevFix with `make run`.
2. Open this `extensions/sunny-devfix-vscode` folder in VS Code.
3. Press `F5` to launch an Extension Development Host.
4. Open a Python file containing `return 'hello ' + username` with a nearby
   `user_name` definition.
5. Open the Problems panel and choose the Sunny DevFix quick fix.

The extension is a supported Python integration, not a universal language
server. It requires the local HTTP engine and does not send source to a cloud
service. VS Code runtime execution was not available in the repository's
automated checks; `node --check extension.js` and the manifest contract tests
are the reproducible checks included here.
