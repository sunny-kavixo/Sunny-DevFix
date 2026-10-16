import json
from pathlib import Path


EXTENSION_DIR = Path("extensions/sunny-devfix-vscode")


def test_vscode_extension_manifest_is_dependency_free_and_wired_to_guardian() -> None:
    manifest = json.loads((EXTENSION_DIR / "package.json").read_text())

    assert manifest["main"] == "./extension.js"
    assert "onLanguage:python" in manifest["activationEvents"]
    assert manifest["contributes"]["commands"][0]["command"] == (
        "sunnyDevFix.analyzeDocument"
    )
    assert manifest["contributes"]["configuration"]["properties"][
        "sunnyDevFix.engineUrl"
    ]["default"] == "http://127.0.0.1:8000"


def test_vscode_extension_uses_local_guardian_and_user_approved_quick_fixes() -> None:
    extension = (EXTENSION_DIR / "extension.js").read_text()

    assert '"/api/guardian"' in extension
    assert "createDiagnosticCollection" in extension
    assert "registerCodeActionsProvider" in extension
    assert "QuickFix" in extension
    assert "WorkspaceEdit" in extension
    assert "http.request" in extension
    assert "eval(" not in extension
