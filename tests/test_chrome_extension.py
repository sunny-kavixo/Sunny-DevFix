import json
from pathlib import Path


EXTENSION_DIR = Path("extensions/sunny-devfix-chrome")


def test_chrome_prototype_is_narrow_and_local_only() -> None:
    manifest = json.loads((EXTENSION_DIR / "manifest.json").read_text())

    assert manifest["manifest_version"] == 3
    assert manifest["host_permissions"] == [
        "http://127.0.0.1:8000/*",
        "http://localhost:8000/*",
    ]
    assert manifest["content_scripts"][0]["matches"] == [
        "http://localhost/*",
        "http://127.0.0.1/*",
    ]


def test_chrome_prototype_uses_guardian_and_requires_a_clicked_fix() -> None:
    script = (EXTENSION_DIR / "content.js").read_text()

    assert "/api/guardian" in script
    assert "Apply approved fix" in script
    assert "dispatchEvent(new Event(\"input\"" in script
    assert "eval(" not in script
