# Sunny DevFix Chrome prototype

This is an explicitly labeled **experimental** Manifest V3 prototype. It is
not a universal browser-editor integration.

## Supported scope

- Runs only on `localhost` and `127.0.0.1` pages.
- Looks for a plain `textarea`, a textarea marked
  `data-sunny-devfix-editor`, or Monaco's input-area selector.
- Sends source only to the local Sunny DevFix engine at
  `http://127.0.0.1:8000/api/guardian`.
- Shows a small diagnostic overlay and applies a proposed fix only after the
  user clicks **Apply approved fix**.

## Load it

1. Run Sunny DevFix with `make run`.
2. Open `chrome://extensions`.
3. Enable **Developer mode**.
4. Choose **Load unpacked** and select this directory.
5. Open a localhost page containing a textarea editor.

The prototype is intentionally narrow because browser editors differ in DOM
ownership, iframes, content security policy, and controlled-input behavior. It
does not claim compatibility with hosted IDEs or arbitrary editors. Chrome
runtime execution is not available in the repository's offline test image;
manifest, JavaScript syntax, and contract tests are included instead.
