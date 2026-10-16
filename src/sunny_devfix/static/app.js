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
  fixedButton.disabled = !suggestion.available;
  diffButton.disabled = !suggestion.available || !comparison.unified_diff;
  document.querySelector("#copy-status").textContent = "";
  fixedButton.dataset.copyValue = comparison.after;
  diffButton.dataset.copyValue = comparison.unified_diff;
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
  sourceInput.focus();
});

sourceInput.addEventListener("input", updateCounts);
tracebackInput.addEventListener("input", updateCounts);
form.addEventListener("submit", analyze);
document.querySelector("#copy-fixed").addEventListener("click", (event) => copyValue(event.currentTarget));
document.querySelector("#copy-diff").addEventListener("click", (event) => copyValue(event.currentTarget));
updateCounts();
