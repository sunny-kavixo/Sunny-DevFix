const EXAMPLES = {
  name_error: {
    source: `def calculate_invoice(subtotal, tax_rate):
    tax = subtotal * tax_rate
    return subtotal + tx

print(calculate_invoice(100.0, 0.08))`,
    traceback: `Traceback (most recent call last):
  File "billing.py", line 5, in <module>
    print(calculate_invoice(100.0, 0.08))
  File "billing.py", line 3, in calculate_invoice
    return subtotal + tx
NameError: name 'tx' is not defined`,
  },
  syntax_error: {
    source: `def format_currency(amount)
    return f"\${amount:,.2f}"

print(format_currency(1250.5))`,
    traceback: `Traceback (most recent call last):
  File "format.py", line 1
    def format_currency(amount)
                               ^
SyntaxError: expected ':'`,
  },
  zero_div: {
    source: `def compute_ratio(total_hits, total_attempts):
    return total_hits / total_attempts

print(compute_ratio(10, 0))`,
    traceback: `Traceback (most recent call last):
  File "stats.py", line 4, in <module>
    print(compute_ratio(10, 0))
  File "stats.py", line 2, in compute_ratio
    return total_hits / total_attempts
ZeroDivisionError: division by zero`,
  },
  index_error: {
    source: `def get_last_token(items):
    return items[len(items)]

print(get_last_token(["alpha", "beta", "gamma"]))`,
    traceback: `Traceback (most recent call last):
  File "tokens.py", line 4, in <module>
    print(get_last_token(["alpha", "beta", "gamma"]))
  File "tokens.py", line 2, in get_last_token
    return items[len(items)]
IndexError: list index out of range`,
  },
};

const sourceInput = document.querySelector("#source-input");
const tracebackInput = document.querySelector("#traceback-input");
const form = document.querySelector("#analysis-form");
const analyzeButton = document.querySelector("#analyze-button");
const agentRepairButton = document.querySelector("#agent-repair-button");
const sourceCount = document.querySelector("#source-count");
const tracebackCount = document.querySelector("#traceback-count");
const emptyState = document.querySelector("#empty-state");
const resultsGrid = document.querySelector("#results-grid");
const errorMessage = document.querySelector("#error-message");
const successMessage = document.querySelector("#agent-success-message");
const analysisState = document.querySelector("#analysis-state");
const guardianState = document.querySelector("#guardian-state");
const guardianEmpty = document.querySelector("#guardian-empty");
const guardianContent = document.querySelector("#guardian-content");
const guardianSummary = document.querySelector("#guardian-summary");
const guardianSource = document.querySelector("#guardian-source");
const guardianDiagnostics = document.querySelector("#guardian-diagnostics");
const modelStatusDot = document.querySelector("#model-status-dot");
const modelStatusText = document.querySelector("#model-status-text");
const modelProviderBadge = document.querySelector("#model-provider-badge");
const agentStateLabel = document.querySelector("#agent-state-label");
const timelineEntriesList = document.querySelector("#timeline-entries-list");
const agentTimelineLog = document.querySelector("#agent-timeline-log");
const agentApplyBtn = document.querySelector("#agent-apply-btn");
const agentRollbackBtn = document.querySelector("#agent-rollback-btn");
const modeNvidiaBtn = document.querySelector("#mode-nvidia-btn");
const modeLocalBtn = document.querySelector("#mode-local-btn");

let useNebiusMode = true;
let guardianTimer = null;
let guardianRequestId = 0;
let currentGuardianDiagnostics = [];
let currentSuggestion = null;
let currentApprovalToken = null;
let currentRollbackToken = null;
let lastRepairResult = null;

function setInferenceMode(useNebius) {
  useNebiusMode = useNebius;
  if (modeNvidiaBtn && modeLocalBtn) {
    modeNvidiaBtn.classList.toggle("active", useNebius);
    modeNvidiaBtn.setAttribute("aria-checked", useNebius ? "true" : "false");
    modeLocalBtn.classList.toggle("active", !useNebius);
    modeLocalBtn.setAttribute("aria-checked", !useNebius ? "true" : "false");
  }
  const btnText = agentRepairButton ? agentRepairButton.querySelector(".button-text") : null;
  if (btnText) {
    btnText.textContent = useNebius ? "AI Repair (NVIDIA)" : "AI Repair (Local AST)";
  } else if (agentRepairButton) {
    agentRepairButton.textContent = useNebius ? "AI Repair (NVIDIA)" : "AI Repair (Local AST)";
  }
  setAgentState(
    "IDLE",
    useNebius
      ? "Provider mode: NVIDIA Nemotron (Nebius Token Factory)"
      : "Provider mode: Local Deterministic AST Engine (Offline)"
  );
}

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
  if (message) successMessage.classList.add("hidden");
}

function setSuccess(message) {
  successMessage.textContent = message;
  successMessage.classList.toggle("hidden", !message);
  if (message) errorMessage.classList.add("hidden");
}

function setAgentState(state, desc = "") {
  agentStateLabel.textContent = `STATE: ${state}`;
  const steps = ["analyzed", "proposed", "approval", "applied", "testing", "verified"];
  const stepMap = {
    IDLE: [],
    ANALYZED: ["analyzed"],
    PATCH_PROPOSED: ["analyzed", "proposed"],
    AWAITING_APPROVAL: ["analyzed", "proposed", "approval"],
    APPLIED: ["analyzed", "proposed", "approval", "applied"],
    TESTING: ["analyzed", "proposed", "approval", "applied", "testing"],
    VERIFIED: ["analyzed", "proposed", "approval", "applied", "testing", "verified"],
    FAILED: ["analyzed"],
    ROLLED_BACK: ["analyzed"],
  };

  const activeSteps = stepMap[state] || [];
  steps.forEach((stepId) => {
    const el = document.querySelector(`#step-${stepId}`);
    if (!el) return;
    el.classList.remove("active", "completed");
    if (activeSteps.includes(stepId)) {
      if (activeSteps[activeSteps.length - 1] === stepId && state !== "VERIFIED") {
        el.classList.add("active");
      } else {
        el.classList.add("completed");
      }
    }
  });

  if (desc) {
    agentTimelineLog.classList.remove("hidden");
    const li = document.createElement("li");
    li.innerHTML = `<strong>[${escapeHtml(state)}]</strong> ${escapeHtml(desc)}`;
    timelineEntriesList.appendChild(li);
  }
}

function formatUnifiedDiff(rawDiff) {
  if (!rawDiff) return "No diff available.";
  return rawDiff
    .split("\n")
    .map((line) => {
      const esc = escapeHtml(line);
      if (line.startsWith("+") && !line.startsWith("+++")) {
        return `<span class="diff-line-add">${esc}</span>`;
      }
      if (line.startsWith("-") && !line.startsWith("---")) {
        return `<span class="diff-line-del">${esc}</span>`;
      }
      if (line.startsWith("@@")) {
        return `<span class="diff-line-hdr">${esc}</span>`;
      }
      return esc;
    })
    .join("\n");
}

async function checkModelInfo() {
  try {
    const res = await fetch("/api/model-info");
    if (!res.ok) throw new Error("Could not check model info");
    const data = await res.json();
    if (data.configured && data.enabled) {
      modelStatusDot.className = "status-dot active-nebius";
      modelStatusText.textContent = `NVIDIA Nemotron · Nebius Token Factory`;
      modelProviderBadge.textContent = "NVIDIA Nemotron";
    } else {
      modelStatusDot.className = "status-dot active-local";
      modelStatusText.textContent = `Local AST Engine (Offline Fallback)`;
      modelProviderBadge.textContent = "AST Engine";
    }
  } catch (err) {
    modelStatusDot.className = "status-dot active-local";
    modelStatusText.textContent = `Local Deterministic Engine`;
    modelProviderBadge.textContent = "AST Engine";
  }
}

function explainResult(result) {
  const type = result.exception_type;
  const message = result.message || "No additional message was provided.";
  const frame = result.deepest_frame;
  const targetLine = result.source_analysis?.target_line;

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

  const context = result.source_analysis?.context || [];
  document.querySelector("#code-context").innerHTML = context.length
    ? context
        .map(
          (line) => `
      <div class="code-line${line.is_target ? " is-target" : ""}">
        <span class="line-number">${line.line_number}</span>
        <span class="line-text">${escapeHtml(line.text)}</span>
      </div>`
        )
        .join("")
    : '<div class="code-line"><span class="line-text">No source line could be mapped.</span></div>';

  const syntaxStatus = document.querySelector("#syntax-status");
  const valid = result.source_analysis?.valid_syntax ?? true;
  syntaxStatus.classList.toggle("is-invalid", !valid);
  syntaxStatus.textContent = valid
    ? "✓ Source syntax parsed successfully"
    : `△ ${result.source_analysis?.syntax_error?.message || "Source syntax needs attention"}`;

  const traceList = document.querySelector("#trace-list");
  const frames = result.frames || [];
  document.querySelector("#frame-count").textContent = `${frames.length} frame${frames.length === 1 ? "" : "s"}`;
  traceList.innerHTML = frames.length
    ? frames
        .map(
          (item, index) => `
      <li class="trace-item">
        <span class="trace-marker">${String(index + 1).padStart(2, "0")}</span>
        <span><span class="trace-file">${escapeHtml(item.filename)}:${item.line_number}</span><span class="trace-function">in ${escapeHtml(item.function)}</span></span>
      </li>`
        )
        .join("")
    : '<li class="trace-item"><span class="trace-marker">—</span><span>No file frame was present.</span></li>';

  if (result.safety?.message) {
    document.querySelector("#safety-message").textContent = result.safety.message;
  }

  if (result.suggestion) {
    renderSuggestion(result.suggestion);
  }
}

function renderSuggestion(suggestion) {
  currentSuggestion = suggestion;
  const comparison = suggestion.comparison || {};
  const confidence = document.querySelector("#suggestion-confidence");
  confidence.textContent = suggestion.available
    ? `${suggestion.confidence} confidence`
    : "Not proposed";
  confidence.classList.toggle("is-confident", suggestion.available);
  document.querySelector("#suggestion-title").textContent = suggestion.title;
  document.querySelector("#suggestion-description").textContent = suggestion.description;
  document.querySelector("#before-code").textContent = comparison.before || "(empty source)";
  document.querySelector("#after-code").textContent = comparison.after || "(empty source)";

  const diffEl = document.querySelector("#diff-output");
  diffEl.innerHTML = formatUnifiedDiff(comparison.unified_diff);

  document.querySelector("#suggestion-limit").textContent =
    suggestion.limitation ||
    (comparison.after_valid_syntax
      ? "✓ Proposed source passes non-executing AST syntax validation."
      : "△ The proposed source needs syntax attention.");

  const fixedButton = document.querySelector("#copy-fixed");
  const diffButton = document.querySelector("#copy-diff");
  const applyButton = document.querySelector("#apply-fixed");
  const evidenceButton = document.querySelector("#verify-evidence");

  applyButton.disabled = !suggestion.available;
  fixedButton.disabled = !suggestion.available;
  diffButton.disabled = !suggestion.available || !comparison.unified_diff;
  evidenceButton.disabled = !suggestion.available || !comparison.changed;
  document.querySelector("#copy-status").textContent = "";
  fixedButton.dataset.copyValue = comparison.after || "";
  diffButton.dataset.copyValue = comparison.unified_diff || "";
}

function renderGuardian(result) {
  currentGuardianDiagnostics = result.diagnostics || [];
  const count = currentGuardianDiagnostics.length;
  guardianState.classList.toggle("is-clean", count === 0 && result.valid_syntax);
  guardianState.classList.toggle("is-alert", count > 0);
  guardianState.textContent =
    count === 0
      ? result.valid_syntax
        ? "No problems found"
        : "Syntax needs attention"
      : `${count} diagnostic${count === 1 ? "" : "s"}`;

  if (!sourceInput.value) {
    guardianEmpty.classList.remove("hidden");
    guardianContent.classList.add("hidden");
    return;
  }

  guardianEmpty.classList.add("hidden");
  guardianContent.classList.remove("hidden");
  guardianSummary.textContent =
    count === 0
      ? "The guardian found no high-confidence issue in this source."
      : "Review each signal before applying a fix. Diagnostics are hypotheses until verified.";

  const byLine = new Map();
  currentGuardianDiagnostics.forEach((item, index) => {
    if (!byLine.has(item.line_number)) byLine.set(item.line_number, []);
    byLine.get(item.line_number).push({ item, index });
  });

  const lines = sourceInput.value.replaceAll("\r\n", "\n").split("\n");
  guardianSource.innerHTML = lines
    .map((line, index) => {
      const lineNumber = index + 1;
      const matches = byLine.get(lineNumber) || [];
      const className = matches.some(({ item }) => item.severity === "error")
        ? " has-error"
        : matches.length
          ? " has-warning"
          : "";
      const title = matches.map(({ item }) => item.message).join(" | ");
      return `<div class="guardian-line${className}" title="${escapeHtml(title)}">
      <span class="guardian-line-number">${lineNumber}</span>
      <span class="guardian-line-text">${escapeHtml(line)}</span>
    </div>`;
    })
    .join("");

  guardianDiagnostics.innerHTML =
    count === 0
      ? '<div class="guardian-diagnostic"><strong>Ready to keep watch.</strong><p>Keep typing; the next pass is debounced to avoid noisy updates.</p></div>'
      : currentGuardianDiagnostics
          .map(
            (item, index) => `
      <div class="guardian-diagnostic ${escapeHtml(item.severity)}" title="${escapeHtml(item.explanation)}">
        <div class="guardian-diagnostic-head">
          <span class="guardian-severity">${escapeHtml(item.severity)} · line ${item.line_number}</span>
          <span class="guardian-confidence">${escapeHtml(item.confidence)} confidence</span>
        </div>
        <strong>${escapeHtml(item.message)}</strong>
        <p>${escapeHtml(item.explanation)}</p>
        ${
          item.fix?.available
            ? `<div class="guardian-fix"><span>Conservative fix available</span><button class="button button-primary button-small guardian-fix-button" type="button" data-guardian-fix="${index}">Review & apply</button></div>`
            : ""
        }
      </div>`
          )
          .join("");

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
  score.classList.toggle(
    "is-confident",
    result.scorecard.overall === "verified" || result.scorecard.overall === "passed"
  );
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
  ]
    .filter(Boolean)
    .join("\n\n");

  document.querySelector("#evidence-output").textContent = output || "No captured output.";
  document.querySelector("#evidence-claim").textContent = result.scorecard.claim;
}

async function verifyEvidence() {
  if (!currentSuggestion?.available) return;
  const card = document.querySelector("#evidence-card");
  card.classList.remove("hidden");
  document.querySelector("#evidence-score").textContent = "running";
  document.querySelector("#evidence-title").textContent = "Running isolated Docker evidence…";
  document.querySelector("#evidence-message").textContent =
    "The before and after versions are being run separately with no network, read-only FS, and memory limits.";
  setAgentState("TESTING", "Executing isolated container evidence reproduction");

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

    if (payload.scorecard?.overall === "verified") {
      setAgentState("VERIFIED", "Isolated container test passed with zero regression");
    } else {
      setAgentState("APPLIED", `Container run finished with result: ${payload.scorecard?.overall}`);
    }
  } catch (error) {
    renderEvidence({
      available: false,
      message: error instanceof Error ? error.message : "Evidence run failed.",
      before: null,
      after: null,
      scorecard: {
        overall: "unavailable",
        claim: "No functional claim was made because the sandbox did not run.",
      },
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
  if (event) event.preventDefault();
  setError("");
  timelineEntriesList.innerHTML = "";

  if (!tracebackInput.value.trim()) {
    setError("Paste a Python traceback before running the analysis.");
    tracebackInput.focus();
    return;
  }

  analyzeButton.disabled = true;
  analyzeButton.innerHTML = 'Reading traceback <span class="button-spinner" aria-hidden="true"></span>';
  analysisState.textContent = "Analyzing locally…";
  analysisState.classList.remove("is-ready");
  setAgentState("ANALYZED", "Inspecting traceback stack and source AST");

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
    analysisState.textContent = "Local analysis ready";
    analysisState.classList.add("is-ready");
    setAgentState("PATCH_PROPOSED", "Generated conservative AST repair proposal");
  } catch (error) {
    resultsGrid.classList.add("hidden");
    emptyState.classList.remove("hidden");
    analysisState.textContent = "Analysis needs attention";
    setError(error instanceof Error ? error.message : "The analysis could not be completed.");
    setAgentState("FAILED", "Analysis encountered an unparseable error");
  } finally {
    analyzeButton.disabled = false;
    analyzeButton.innerHTML = "Local Analyze";
  }
}

async function runAgentRepair() {
  setError("");
  timelineEntriesList.innerHTML = "";

  if (!tracebackInput.value.trim()) {
    setError("Paste a Python traceback to initiate AI agent repair.");
    tracebackInput.focus();
    return;
  }

  agentRepairButton.disabled = true;
  agentRepairButton.innerHTML = useNebiusMode
    ? 'Reasoning with NVIDIA… <span class="button-spinner" aria-hidden="true"></span>'
    : 'Synthesizing local repair… <span class="button-spinner" aria-hidden="true"></span>';
  analysisState.textContent = useNebiusMode
    ? "Synthesizing repair via NVIDIA Nemotron…"
    : "Synthesizing repair via Local AST Engine…";
  setAgentState("ANALYZED", "Step 1: Mapping traceback frames to source code");

  try {
    const response = await fetch("/api/agent/repair", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        source: sourceInput.value,
        traceback: tracebackInput.value,
        use_nebius: useNebiusMode,
      }),
    });

    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.detail || payload.error || "Agent repair failed.");
    }

    if (payload.repair) {
      lastRepairResult = payload.repair;
      const r = payload.repair;

      // Update Explanation UI
      document.querySelector("#explanation-title").textContent = r.root_cause_title;
      document.querySelector("#explanation-copy").textContent = r.root_cause_explanation;
      document.querySelector("#next-step").textContent = r.next_step;
      modelProviderBadge.textContent = `${r.provider} (${r.model})`;

      // Render Suggestion
      renderSuggestion({
        available: r.available,
        title: r.root_cause_title,
        description: r.fix_description,
        confidence: r.confidence,
        comparison: {
          before: r.before_source,
          after: r.after_source,
          unified_diff: r.unified_diff,
          changed: r.before_source !== r.after_source,
          before_valid_syntax: true,
          after_valid_syntax: r.syntax_valid,
        },
        limitation: r.syntax_valid
          ? "✓ Proposed repair passed syntax AST verification."
          : "△ Warning: proposed repair may need manual review.",
      });

      if (payload.patch_preview) {
        currentApprovalToken = payload.patch_preview.approval_id;
        agentApplyBtn.classList.remove("hidden");
      } else {
        agentApplyBtn.classList.add("hidden");
      }

      emptyState.classList.add("hidden");
      resultsGrid.classList.remove("hidden");
      analysisState.textContent = `Repair proposed by ${r.provider}`;
      analysisState.classList.add("is-ready");

      setAgentState(payload.state, `Proposed repair: ${r.fix_description}`);
    } else {
      throw new Error(payload.error || "No repair was synthesized.");
    }
  } catch (error) {
    setError(error instanceof Error ? error.message : "Agent repair request failed.");
    setAgentState("FAILED", error instanceof Error ? error.message : "Repair failed");
  } finally {
    agentRepairButton.disabled = false;
    agentRepairButton.innerHTML = `<span class="button-icon">⚡</span><span class="button-text">${useNebiusMode ? "AI Repair (NVIDIA)" : "AI Repair (Local AST)"}</span>`;
  }
}

async function applyAgentPatch() {
  if (!currentApprovalToken) {
    setError("No active patch approval token exists.");
    return;
  }

  const confirmed = window.confirm(
    "Human Approval Required:\n\nAre you sure you want to write this patch to the workspace disk?\nThis operation is protected by a one-time rollback token."
  );
  if (!confirmed) {
    setAgentState("AWAITING_APPROVAL", "Patch write cancelled by user");
    return;
  }

  setAgentState("APPLIED", "Applying patch atomically to authorized workspace target");
  try {
    const response = await fetch("/api/agent/apply", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        token: currentApprovalToken,
        confirm: true,
        source_before: lastRepairResult?.before_source || "",
        source_after: lastRepairResult?.after_source || "",
      }),
    });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.detail || payload.error || "Failed to apply patch");

    if (payload.patch_result?.rollback_id) {
      currentRollbackToken = payload.patch_result.rollback_id;
      agentRollbackBtn.classList.remove("hidden");
      agentApplyBtn.classList.add("hidden");
      setSuccess(`✓ Patch applied successfully to ${payload.patch_result.relative_path}. One-click rollback token active.`);
    }

    if (payload.evidence) {
      renderEvidence(payload.evidence);
    }
  } catch (err) {
    setError(err instanceof Error ? err.message : "Failed to apply patch.");
    setAgentState("FAILED", "Patch application error");
  }
}

async function rollbackAgentPatch() {
  if (!currentRollbackToken) {
    setError("No active rollback token exists.");
    return;
  }

  const confirmed = window.confirm(
    "Human Approval Required:\n\nDo you want to roll back this patch and restore the exact pre-patch code?"
  );
  if (!confirmed) return;

  try {
    const response = await fetch("/api/agent/rollback", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        token: currentRollbackToken,
        confirm: true,
      }),
    });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.detail || "Rollback failed");

    setAgentState("ROLLED_BACK", `Restored pre-patch state for ${payload.relative_path}`);
    agentRollbackBtn.classList.add("hidden");
    setSuccess(`✓ Successfully rolled back ${payload.relative_path} to exact pre-patch content.`);
  } catch (err) {
    setError(err instanceof Error ? err.message : "Rollback failed.");
  }
}

// Event Listeners
document.querySelector("#load-demo").addEventListener("click", () => {
  const select = document.querySelector("#example-select");
  const key = select.value;
  const ex = EXAMPLES[key] || EXAMPLES.name_error;
  sourceInput.value = ex.source;
  tracebackInput.value = ex.traceback;
  updateCounts();
  scheduleGuardian();
  sourceInput.focus();
  setAgentState("IDLE", `Loaded ${select.options[select.selectedIndex].text}`);
});

document.querySelector("#clear-form").addEventListener("click", () => {
  sourceInput.value = "";
  tracebackInput.value = "";
  updateCounts();
  setError("");
  successMessage.classList.add("hidden");
  emptyState.classList.remove("hidden");
  resultsGrid.classList.add("hidden");
  analysisState.textContent = "Waiting for analysis or repair request";
  analysisState.classList.remove("is-ready");
  guardianState.textContent = "Waiting for source";
  guardianState.classList.remove("is-clean", "is-alert");
  guardianEmpty.textContent = "Type or paste Python to see instant syntax warnings and validated quick fixes.";
  guardianEmpty.classList.remove("hidden");
  guardianContent.classList.add("hidden");
  document.querySelector("#evidence-card").classList.add("hidden");
  agentApplyBtn.classList.add("hidden");
  agentRollbackBtn.classList.add("hidden");
  setAgentState("IDLE", "Workspace cleared");
  sourceInput.focus();
});

sourceInput.addEventListener("input", () => {
  updateCounts();
  scheduleGuardian();
});
tracebackInput.addEventListener("input", updateCounts);
form.addEventListener("submit", analyze);
agentRepairButton.addEventListener("click", runAgentRepair);
document.querySelector("#apply-fixed").addEventListener("click", applyCurrentFix);
document.querySelector("#verify-evidence").addEventListener("click", verifyEvidence);
agentApplyBtn.addEventListener("click", applyAgentPatch);
agentRollbackBtn.addEventListener("click", rollbackAgentPatch);
document.querySelector("#copy-fixed").addEventListener("click", (event) => copyValue(event.currentTarget));
document.querySelector("#copy-diff").addEventListener("click", (event) => copyValue(event.currentTarget));

if (modeNvidiaBtn) {
  modeNvidiaBtn.addEventListener("click", () => setInferenceMode(true));
}
if (modeLocalBtn) {
  modeLocalBtn.addEventListener("click", () => setInferenceMode(false));
}

// Startup
updateCounts();
checkModelInfo();
setAgentState("IDLE", "System initialized and ready");

// URL Query Parameter Support for Evaluators
const urlParams = new URLSearchParams(window.location.search);
const initialExample = urlParams.get("example") || (urlParams.get("demo") ? "name_error" : null);
if (initialExample && EXAMPLES[initialExample]) {
  const ex = EXAMPLES[initialExample];
  sourceInput.value = ex.source;
  tracebackInput.value = ex.traceback;
  const select = document.querySelector("#example-select");
  if (select) select.value = initialExample;
  updateCounts();
  scheduleGuardian();
  if (urlParams.get("autorun") === "true") {
    setTimeout(() => {
      runAgentRepair();
    }, 150);
  }
}

