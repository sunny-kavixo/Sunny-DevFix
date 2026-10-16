"use strict";

const http = require("http");
const vscode = require("vscode");

const timers = new Map();
const diagnosticData = new Map();

function activate(context) {
  const diagnostics = vscode.languages.createDiagnosticCollection("sunny-devfix");
  context.subscriptions.push(diagnostics);

  const schedule = (document) => scheduleDocument(document, diagnostics);
  context.subscriptions.push(vscode.workspace.onDidOpenTextDocument(schedule));
  context.subscriptions.push(vscode.workspace.onDidChangeTextDocument((event) => schedule(event.document)));
  context.subscriptions.push(vscode.workspace.onDidCloseTextDocument((document) => {
    clearTimeout(timers.get(document.uri.toString()));
    timers.delete(document.uri.toString());
    diagnosticData.delete(document.uri.toString());
    diagnostics.delete(document.uri);
  }));
  context.subscriptions.push(vscode.commands.registerCommand("sunnyDevFix.analyzeDocument", () => {
    const editor = vscode.window.activeTextEditor;
    if (editor) return analyzeDocument(editor.document, diagnostics);
    return undefined;
  }));
  context.subscriptions.push(vscode.languages.registerCodeActionsProvider(
    { language: "python" },
    { provideCodeActions: (document, range) => provideCodeActions(document, range) },
    { providedCodeActionKinds: [vscode.CodeActionKind.QuickFix] },
  ));

  vscode.workspace.textDocuments.filter((document) => document.languageId === "python").forEach(schedule);
}

function scheduleDocument(document, diagnostics) {
  if (document.languageId !== "python") return;
  const key = document.uri.toString();
  clearTimeout(timers.get(key));
  const delay = vscode.workspace.getConfiguration("sunnyDevFix").get("debounceMilliseconds", 450);
  timers.set(key, setTimeout(() => analyzeDocument(document, diagnostics), delay));
}

async function analyzeDocument(document, diagnostics) {
  try {
    const result = await postJson("/api/guardian", { source: document.getText() });
    const items = result.diagnostics || [];
    diagnosticData.set(document.uri.toString(), items);
    diagnostics.set(document.uri, items.map((item) => toDiagnostic(item)));
  } catch (error) {
    diagnosticData.delete(document.uri.toString());
    diagnostics.delete(document.uri);
    console.warn(`Sunny DevFix engine unavailable: ${error.message}`);
  }
}

function toDiagnostic(item) {
  const line = Math.max(0, item.line_number - 1);
  const column = Math.max(0, (item.column || 1) - 1);
  const severity = item.severity === "error"
    ? vscode.DiagnosticSeverity.Error
    : vscode.DiagnosticSeverity.Warning;
  const diagnostic = new vscode.Diagnostic(
    new vscode.Range(line, column, line, column + 1),
    `${item.message} (${item.confidence} confidence)`,
    severity,
  );
  diagnostic.code = item.code;
  diagnostic.source = "Sunny DevFix";
  return diagnostic;
}

function provideCodeActions(document, range) {
  const items = diagnosticData.get(document.uri.toString()) || [];
  return items
    .filter((item) => item.fix && item.fix.available)
    .filter((item) => range.start.line <= item.line_number - 1 && range.end.line >= item.line_number - 1)
    .map((item) => {
      const action = new vscode.CodeAction(
        `Sunny DevFix: ${item.fix.title}`,
        vscode.CodeActionKind.QuickFix,
      );
      action.diagnostics = [toDiagnostic(item)];
      action.isPreferred = true;
      const fullRange = new vscode.Range(
        document.positionAt(0),
        document.positionAt(document.getText().length),
      );
      action.edit = new vscode.WorkspaceEdit();
      action.edit.replace(document.uri, fullRange, item.fix.comparison.after);
      return action;
    });
}

function postJson(path, body) {
  const base = vscode.workspace.getConfiguration("sunnyDevFix").get("engineUrl", "http://127.0.0.1:8000");
  const url = new URL(path, base.endsWith("/") ? base : `${base}/`);
  const payload = JSON.stringify(body);
  return new Promise((resolve, reject) => {
    const request = http.request({
      hostname: url.hostname,
      port: url.port || 80,
      path: `${url.pathname}${url.search}`,
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Content-Length": Buffer.byteLength(payload),
      },
      timeout: 2500,
    }, (response) => {
      let data = "";
      response.setEncoding("utf8");
      response.on("data", (chunk) => { data += chunk; });
      response.on("end", () => {
        if (response.statusCode < 200 || response.statusCode >= 300) {
          reject(new Error(`HTTP ${response.statusCode}: ${data.slice(0, 200)}`));
          return;
        }
        try {
          resolve(JSON.parse(data));
        } catch (error) {
          reject(new Error(`Invalid engine response: ${error.message}`));
        }
      });
    });
    request.on("timeout", () => request.destroy(new Error("Sunny DevFix request timed out")));
    request.on("error", reject);
    request.write(payload);
    request.end();
  });
}

function deactivate() {
  timers.forEach((timer) => clearTimeout(timer));
  timers.clear();
}

module.exports = { activate, deactivate };
