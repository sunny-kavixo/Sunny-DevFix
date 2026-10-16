"use strict";

const ENGINE = "http://127.0.0.1:8000/api/guardian";
let editor = null;
let timer = null;
let latestDiagnostics = [];

function findEditor() {
  return document.querySelector("textarea.monaco-editor textarea.inputarea")
    || document.querySelector("textarea[data-sunny-devfix-editor]")
    || document.querySelector("textarea");
}

function mountPanel() {
  if (document.querySelector("#sunny-devfix-chrome-panel")) return;
  const panel = document.createElement("aside");
  panel.id = "sunny-devfix-chrome-panel";
  panel.innerHTML = `
    <div class="sunny-devfix-chrome-title"><span>✦</span> Sunny DevFix <small>prototype</small></div>
    <div class="sunny-devfix-chrome-state" data-state>Finds a local text editor…</div>
    <div class="sunny-devfix-chrome-list" data-list></div>`;
  document.body.appendChild(panel);
}

function setState(message, kind = "") {
  const state = document.querySelector("[data-state]");
  if (!state) return;
  state.textContent = message;
  state.dataset.kind = kind;
}

function escapeText(value) {
  return String(value).replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;");
}

function renderDiagnostics(diagnostics) {
  const list = document.querySelector("[data-list]");
  if (!list) return;
  latestDiagnostics = diagnostics;
  if (!diagnostics.length) {
    list.innerHTML = "<div class=\"sunny-devfix-chrome-clean\">No local signals.</div>";
    return;
  }
  list.innerHTML = diagnostics.slice(0, 4).map((item, index) => `
    <div class="sunny-devfix-chrome-item">
      <strong>${escapeText(item.severity)} · line ${item.line_number}</strong>
      <span>${escapeText(item.message)}</span>
      ${item.fix?.available ? `<button type="button" data-fix="${index}">Apply approved fix</button>` : ""}
    </div>`).join("");
  list.querySelectorAll("[data-fix]").forEach((button) => {
    button.addEventListener("click", () => applyFix(Number(button.dataset.fix)));
  });
}

function applyFix(index) {
  const after = latestDiagnostics[index]?.fix?.comparison?.after;
  if (!editor || !after) return;
  const setter = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, "value").set;
  setter.call(editor, after);
  editor.dispatchEvent(new Event("input", { bubbles: true }));
  setState("Fix applied locally; rechecking…", "ok");
  diagnose();
}

async function diagnose() {
  if (!editor) {
    setState("No supported textarea editor found", "muted");
    return;
  }
  setState("Checking locally…");
  try {
    const response = await fetch(ENGINE, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ source: editor.value }),
    });
    if (!response.ok) throw new Error(`Engine HTTP ${response.status}`);
    const result = await response.json();
    renderDiagnostics(result.diagnostics || []);
    setState(result.diagnostics?.length ? `${result.diagnostics.length} signal(s)` : "No problems found", result.diagnostics?.length ? "warn" : "ok");
  } catch (error) {
    setState("Local engine unavailable", "error");
    renderDiagnostics([]);
  }
}

function schedule() {
  clearTimeout(timer);
  timer = setTimeout(diagnose, 500);
}

function boot() {
  editor = findEditor();
  mountPanel();
  if (!editor) {
    setState("Prototype supports localhost textareas and Monaco input areas", "muted");
    return;
  }
  editor.addEventListener("input", schedule);
  diagnose();
}

boot();
