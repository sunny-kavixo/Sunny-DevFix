const DEMO_SOURCE = `def greet(user_name):
    return "Hello, " + username

print(greet("Sunny"))`;

const DEMO_TRACEBACK = `Traceback (most recent call last):
  File "demo.py", line 4, in <module>
    print(greet("Sunny"))
  File "demo.py", line 2, in greet
    return "Hello, " + username
NameError: name 'username' is not defined`;

const sourceInput = document.querySelector("#source-input");
const tracebackInput = document.querySelector("#traceback-input");
const form = document.querySelector("#analysis-form");
const analyzeButton = document.querySelector("#analyze-button");
const sourceCount = document.querySelector("#source-count");
const tracebackCount = document.querySelector("#traceback-count");
const emptyState = document.querySelector("#empty-state");
const resultsGrid = document.querySelector("#results-grid");
const errorMessage = document.querySelector("#error-message");
const analysisState = document.querySelector("#analysis-state");
const guardianState = document.querySelector("#guardian-state");
const guardianEmpty = document.querySelector("#guardian-empty");
const guardianContent = document.querySelector("#guardian-content");
const guardianSummary = document.querySelector("#guardian-summary");
const guardianSource = document.querySelector("#guardian-source");
const guardianDiagnostics = document.querySelector("#guardian-diagnostics");
let guardianTimer = null;
let guardianRequestId = 0;
let currentGuardianDiagnostics = [];
let currentSuggestion = null;

function updateCount(input, output) {
  output.textContent = `${input.value.length.toLocaleString()} / 20,000`;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function updateCounts() {
  updateCount(sourceInput, sourceCount);
  updateCount(tracebackInput, tracebackCount);
}

function setError(message) {
  errorMessage.textContent = message;
  errorMessage.classList.toggle("hidden", !message);
}

function explainResult(result) {
  const type = result.exception_type;
  const message = result.message || "No additional message was provided.";
  const frame = result.deepest_frame;
  const targetLine = result.source_analysis.target_line;

  document.querySelector("#exception-type").textContent = type;
  document.querySelector("#exception-message").textContent = message;
  document.querySelector("#exception-location").textContent = frame
    ? `${frame.filename}:${frame.line_number} · ${frame.function}`
    : "No traceback frame mapped";

  const rootCause = result.root_cause || {
    title: "Python stopped at this exception",
    explanation: "Start with the deepest traceback frame and inspect the values flowing into it.",
    next_step: "Inspect the highlighted source line.",
  };
  document.querySelector("#explanation-title").textContent = rootCause.title;
  document.querySelector("#explanation-copy").textContent = `${rootCause.explanation} The traceback message is: “${message}”`;
  document.querySelector("#next-step").textContent = targetLine
    ? `${rootCause.next_step} Focus line ${targetLine}.`
    : rootCause.next_step;

  const context = result.source_analysis.context;
  document.querySelector("#code-context").innerHTML = context.length
    ? context.map((line) => `
      <div class="code-line${line.is_target ? " is-target" : ""}">
        <span class="line-number">${line.line_number}</span>
        <span class="line-text">${escapeHtml(line.text)}</span>
      </div>`).join("")
    : '<div class="code-line"><span class="line-text">No source line could be mapped.</span></div>';

  const syntaxStatus = document.querySelector("#syntax-status");
  syntaxStatus.classList.toggle("is-invalid", !result.source_analysis.valid_syntax);
  syntaxStatus.textContent = result.source_analysis.valid_syntax
    ? "✓ Source syntax parsed successfully"
    : `△ ${result.source_analysis.syntax_error?.message || "Source syntax needs attention"}`;

  const traceList = document.querySelector("#trace-list");
  document.querySelector("#frame-count").textContent = `${result.frames.length} frame${result.frames.length === 1 ? "" : "s"}`;
  traceList.innerHTML = result.frames.length
    ? result.frames.map((item, index) => `
      <li class="trace-item">
        <span class="trace-marker">${String(index + 1).padStart(2, "0")}</span>
        <span><span class="trace-file">${escapeHtml(item.filename)}:${item.line_number}</span><span class="trace-function">in ${escapeHtml(item.function)}</span></span>
      </li>`).join("")
    : '<li class="trace-item"><span class="trace-marker">—</span><span>No file frame was present.</span></li>';

  document.querySelector("#safety-message").textContent = result.safety.message;
  renderSuggestion(result.suggestion);
}

function renderSuggestion(suggestion) {
  currentSuggestion = suggestion;
  const comparison = suggestion.comparison;
  const confidence = document.querySelector("#suggestion-confidence");
  confidence.textContent = suggestion.available
    ? `${suggestion.confidence} confidence`
    : "Not proposed";
  confidence.classList.toggle("is-confident", suggestion.available);
  document.querySelector("#suggestion-title").textContent = suggestion.title;
  document.querySelector("#suggestion-description").textContent = suggestion.description;
  document.querySelector("#before-code").textContent = comparison.before || "(empty source)";
  document.querySelector("#after-code").textContent = comparison.after || "(empty source)";
  document.querySelector("#diff-output").textContent = comparison.unified_diff || "No diff available.";
  document.querySelector("#suggestion-limit").textContent = suggestion.limitation || (
    comparison.after_valid_syntax
      ? "✓ Proposed source passes non-executing syntax validation."
      : "△ The proposed source needs syntax attention."
  );

  const fixedButton = document.querySelector("#copy-fixed");
  const diffButton = document.querySelector("#copy-diff");
  const applyButton = document.querySelector("#apply-fixed");
  const evidenceButton = document.querySelector("#verify-evidence");
  applyButton.disabled = !suggestion.available;
  fixedButton.disabled = !suggestion.available;
  diffButton.disabled = !suggestion.available || !comparison.unified_diff;
  evidenceButton.disabled = !suggestion.available || !comparison.changed;
  document.querySelector("#copy-status").textContent = "";
  fixedButton.dataset.copyValue = comparison.after;
  diffButton.dataset.copyValue = comparison.unified_diff;
}

function renderGuardian(result) {
  currentGuardianDiagnostics = result.diagnostics || [];
  const count = currentGuardianDiagnostics.length;
  guardianState.classList.toggle("is-clean", count === 0 && result.valid_syntax);
  guardianState.classList.toggle("is-alert", count > 0);
  guardianState.textContent = count === 0
    ? (result.valid_syntax ? "No problems found" : "Syntax needs attention")
    : `${count} diagnostic${count === 1 ? "" : "s"}`;

  if (!sourceInput.value) {
    guardianEmpty.classList.remove("hidden");
    guardianContent.classList.add("hidden");
    return;
  }

  guardianEmpty.classList.add("hidden");
  guardianContent.classList.remove("hidden");
  guardianSummary.textContent = count === 0
    ? "The guardian found no high-confidence issue in this source."
    : "Review each signal before applying a fix. Diagnostics are hypotheses until verified.";

  const byLine = new Map();
  currentGuardianDiagnostics.forEach((item, index) => {
    if (!byLine.has(item.line_number)) byLine.set(item.line_number, []);
    byLine.get(item.line_number).push({ item, index });
  });
  const lines = sourceInput.value.replaceAll("\r\n", "\n").split("\n");
  guardianSource.innerHTML = lines.map((line, index) => {
    const lineNumber = index + 1;
    const matches = byLine.get(lineNumber) || [];
    const className = matches.some(({ item }) => item.severity === "error")
      ? " has-error"
      : matches.length ? " has-warning" : "";
    const title = matches.map(({ item }) => item.message).join(" | ");
    return `<div class="guardian-line${className}" title="${escapeHtml(title)}">
      <span class="guardian-line-number">${lineNumber}</span>
      <span class="guardian-line-text">${escapeHtml(line)}</span>
    </div>`;
  }).join("");

  guardianDiagnostics.innerHTML = count === 0
    ? '<div class="guardian-diagnostic"><strong>Ready to keep watch.</strong><p>Keep typing; the next pass is debounced to avoid noisy updates.</p></div>'
    : currentGuardianDiagnostics.map((item, index) => `
      <div class="guardian-diagnostic ${escapeHtml(item.severity)}" title="${escapeHtml(item.explanation)}">
        <div class="guardian-diagnostic-head">
          <span class="guardian-severity">${escapeHtml(item.severity)} · line ${item.line_number}</span>
          <span class="guardian-confidence">${escapeHtml(item.confidence)} confidence</span>
        </div>
        <strong>${escapeHtml(item.message)}</strong>
        <p>${escapeHtml(item.explanation)}</p>
        ${item.fix?.available ? `<div class="guardian-fix"><span>Conservative fix available</span><button class="button button-primary button-small guardian-fix-button" type="button" data-guardian-fix="${index}">Review & apply</button></div>` : ""}
      </div>`).join("");
  guardianDiagnostics.querySelectorAll("[data-guardian-fix]").forEach((button) => {
    button.addEventListener("click", () => applyGuardianFix(Number(button.dataset.guardianFix)));
  });
}

async function runGuardian() {
  const source = sourceInput.value;
  const requestId = ++guardianRequestId;
  if (!source) {
    currentGuardianDiagnostics = [];
    guardianState.textContent = "Waiting for source";
    guardianState.classList.remove("is-clean", "is-alert");
    guardianEmpty.classList.remove("hidden");
    guardianContent.classList.add("hidden");
    return;
  }
  guardianState.textContent = "Checking locally…";
  guardianState.classList.remove("is-clean", "is-alert");
  try {
    const response = await fetch("/api/guardian", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ source }),
    });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.detail || "Guardian check failed.");
    if (requestId === guardianRequestId) renderGuardian(payload);
  } catch (error) {
    if (requestId !== guardianRequestId) return;
    guardianState.textContent = "Guardian unavailable";
    guardianState.classList.add("is-alert");
    guardianEmpty.textContent = error instanceof Error ? error.message : "Guardian check failed.";
    guardianEmpty.classList.remove("hidden");
    guardianContent.classList.add("hidden");
  }
}

function scheduleGuardian() {
  window.clearTimeout(guardianTimer);
  guardianTimer = window.setTimeout(runGuardian, 420);
}

function applyGuardianFix(index) {
  const diagnostic = currentGuardianDiagnostics[index];
  const fixed = diagnostic?.fix?.comparison?.after;
  if (!fixed) return;
  sourceInput.value = fixed;
  updateCounts();
  sourceInput.focus();
  scheduleGuardian();
  if (tracebackInput.value.trim()) form.requestSubmit();
}

function applyCurrentFix() {
  const fixed = currentSuggestion?.comparison?.after;
  if (!fixed || !currentSuggestion.available) return;
  sourceInput.value = fixed;
  updateCounts();
  sourceInput.focus();
  scheduleGuardian();
  form.requestSubmit();
}

function renderEvidence(result) {
  const card = document.querySelector("#evidence-card");
  card.classList.remove("hidden");
  const score = document.querySelector("#evidence-score");
  score.textContent = result.scorecard.overall;
  score.classList.toggle("is-confident", result.scorecard.overall === "verified" || result.scorecard.overall === "passed");
  document.querySelector("#evidence-title").textContent = result.available
    ? "What the isolated reproduction showed"
    : "Evidence lab unavailable";
  document.querySelector("#evidence-message").textContent = result.message;
  const before = result.before;
  const after = result.after;
  document.querySelector("#evidence-before-status").textContent = before?.status || "Not run";
  document.querySelector("#evidence-after-status").textContent = after?.status || "Not run";
  document.querySelector("#evidence-before-detail").textContent = before
    ? `${before.duration_ms} ms · exit ${before.exit_code ?? "—"}`
    : "No container started";
  document.querySelector("#evidence-after-detail").textContent = after
    ? `${after.duration_ms} ms · exit ${after.exit_code ?? "—"}`
    : "No container started";
  const output = [
    before?.stdout ? `BEFORE stdout:\n${before.stdout}` : "",
    before?.stderr ? `BEFORE stderr:\n${before.stderr}` : "",
    after?.stdout ? `AFTER stdout:\n${after.stdout}` : "",
    after?.stderr ? `AFTER stderr:\n${after.stderr}` : "",
  ].filter(Boolean).join("\n\n");
  document.querySelector("#evidence-output").textContent = output || "No captured output.";
  document.querySelector("#evidence-claim").textContent = result.scorecard.claim;
}

async function verifyEvidence() {
  if (!currentSuggestion?.available) return;
  const card = document.querySelector("#evidence-card");
  card.classList.remove("hidden");
  document.querySelector("#evidence-score").textContent = "running";
  document.querySelector("#evidence-title").textContent = "Running isolated Docker evidence…";
  document.querySelector("#evidence-message").textContent = "The before and after versions are being run separately with no network or host mount.";
  try {
    const comparison = currentSuggestion.comparison;
    const response = await fetch("/api/evidence", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        source_before: comparison.before,
        source_after: comparison.after,
        confirm: true,
      }),
    });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.detail || "Evidence run failed.");
    renderEvidence(payload);
  } catch (error) {
    renderEvidence({
      available: false,
      message: error instanceof Error ? error.message : "Evidence run failed.",
      before: null,
      after: null,
      scorecard: { overall: "unavailable", claim: "No functional claim was made because the sandbox did not run." },
    });
  }
}

async function copyValue(button) {
  const value = button.dataset.copyValue || "";
  if (!value || button.disabled) return;
  try {
    await navigator.clipboard.writeText(value);
    document.querySelector("#copy-status").textContent = "Copied";
  } catch (error) {
    document.querySelector("#copy-status").textContent = "Copy unavailable";
  }
}

async function analyze(event) {
  event.preventDefault();
  setError("");

  if (!tracebackInput.value.trim()) {
    setError("Paste a Python traceback before running the analysis.");
    tracebackInput.focus();
    return;
  }

  analyzeButton.disabled = true;
  analyzeButton.innerHTML = 'Reading traceback <span class="button-spinner" aria-hidden="true"></span>';
  analysisState.textContent = "Analyzing locally…";
  analysisState.classList.remove("is-ready");

  try {
    const response = await fetch("/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ source: sourceInput.value, traceback: tracebackInput.value }),
    });
    const payload = await response.json();
    if (!response.ok) {
      const detail = typeof payload.detail === "string" ? payload.detail : "The request could not be analyzed.";
      throw new Error(detail);
    }
    explainResult(payload);
    emptyState.classList.add("hidden");
    resultsGrid.classList.remove("hidden");
    analysisState.textContent = "Analysis ready";
    analysisState.classList.add("is-ready");
  } catch (error) {
    resultsGrid.classList.add("hidden");
    emptyState.classList.remove("hidden");
    analysisState.textContent = "Analysis needs attention";
    setError(error instanceof Error ? error.message : "The analysis could not be completed.");
  } finally {
    analyzeButton.disabled = false;
    analyzeButton.innerHTML = 'Analyze traceback <span aria-hidden="true">→</span>';
  }
}

document.querySelector("#load-demo").addEventListener("click", () => {
  sourceInput.value = DEMO_SOURCE;
  tracebackInput.value = DEMO_TRACEBACK;
  updateCounts();
  scheduleGuardian();
  sourceInput.focus();
});

document.querySelector("#clear-form").addEventListener("click", () => {
  sourceInput.value = "";
  tracebackInput.value = "";
  updateCounts();
  setError("");
  emptyState.classList.remove("hidden");
  resultsGrid.classList.add("hidden");
  analysisState.textContent = "Waiting for a traceback";
  analysisState.classList.remove("is-ready");
  guardianState.textContent = "Waiting for source";
  guardianState.classList.remove("is-clean", "is-alert");
  guardianEmpty.textContent = "Type or paste Python to see conservative warnings and approved quick fixes.";
  guardianEmpty.classList.remove("hidden");
  guardianContent.classList.add("hidden");
  document.querySelector("#evidence-card").classList.add("hidden");
  sourceInput.focus();
});

sourceInput.addEventListener("input", () => {
  updateCounts();
  scheduleGuardian();
});
tracebackInput.addEventListener("input", updateCounts);
form.addEventListener("submit", analyze);
document.querySelector("#apply-fixed").addEventListener("click", applyCurrentFix);
document.querySelector("#verify-evidence").addEventListener("click", verifyEvidence);
document.querySelector("#copy-fixed").addEventListener("click", (event) => copyValue(event.currentTarget));
document.querySelector("#copy-diff").addEventListener("click", (event) => copyValue(event.currentTarget));
updateCounts();
