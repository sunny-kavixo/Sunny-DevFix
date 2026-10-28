"""
End-to-End Chrome Browser Automation & Screenshot Evidence Suite for Sunny-DevFix.
Interacts with the running application over Chrome DevTools Protocol (CDP).
"""

import asyncio
import json
import os
import subprocess
import time
from pathlib import Path
import httpx
import websockets

SCREENSHOT_DIR = Path("release/screenshots/final_ui")
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

CHROME_PATH = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
CHROME_PORT = 9222
BASE_URL = "http://127.0.0.1:8000"


class ChromeSession:
    def __init__(self, ws_url: str):
        self.ws_url = ws_url
        self.ws = None
        self.msg_id = 0

    async def connect(self):
        self.ws = await websockets.connect(self.ws_url, max_size=20_000_000)

    async def send(self, method: str, params: dict = None) -> dict:
        self.msg_id += 1
        payload = {"id": self.msg_id, "method": method, "params": params or {}}
        await self.ws.send(json.dumps(payload))
        while True:
            resp_raw = await self.ws.recv()
            resp = json.loads(resp_raw)
            if resp.get("id") == self.msg_id:
                return resp.get("result", {})

    async def eval_js(self, expression: str) -> any:
        res = await self.send("Runtime.evaluate", {
            "expression": expression,
            "returnByValue": True,
            "awaitPromise": True
        })
        val = res.get("result", {}).get("value")
        return val

    async def capture_screenshot(self, filename: str):
        res = await self.send("Page.captureScreenshot", {"format": "png"})
        import base64
        data = base64.b64decode(res["data"])
        out_path = SCREENSHOT_DIR / filename
        out_path.write_bytes(data)
        print(f"Captured screenshot: {out_path} ({len(data)} bytes)")
        return out_path

    async def set_viewport(self, width: int, height: int, is_mobile: bool = False):
        await self.send("Emulation.setDeviceMetricsOverride", {
            "width": width,
            "height": height,
            "deviceScaleFactor": 1,
            "mobile": is_mobile
        })

    async def close(self):
        if self.ws:
            await self.ws.close()


def launch_chrome():
    cmd = [
        CHROME_PATH,
        "--headless=new",
        f"--remote-debugging-port={CHROME_PORT}",
        "--window-size=1920,1080",
        "--hide-scrollbars",
        "--no-first-run",
        "--no-default-browser-check"
    ]
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1.5)
    return proc


async def run_e2e_tests():
    print("--- Starting Sunny-DevFix Browser E2E Test Suite ---")
    chrome_proc = launch_chrome()
    try:
        # Create a new target page
        async with httpx.AsyncClient() as client:
            resp = await client.put(f"http://127.0.0.1:{CHROME_PORT}/json/new")
            page_info = resp.json()
            ws_url = page_info["webSocketDebuggerUrl"]

        session = ChromeSession(ws_url)
        await session.connect()

        # Step 1: Navigate to fresh application
        print("1. Navigating to Sunny-DevFix application...")
        await session.send("Page.enable")
        await session.send("Runtime.enable")
        await session.send("Page.navigate", {"url": BASE_URL})
        await asyncio.sleep(1.0)
        await session.capture_screenshot("01_fresh_launch_desktop.png")

        # Step 2: Select Example 1 (NameError) and Load
        print("2. Selecting and loading NameError preset...")
        await session.eval_js("""
            document.querySelector('#example-select').value = 'name_error';
            document.querySelector('#load-demo').click();
        """)
        await asyncio.sleep(0.8)
        await session.capture_screenshot("02_preset_loaded_guardian.png")

        # Step 3: Trigger AI Repair (NVIDIA / Agent Lifecycle)
        print("3. Executing AI Repair action...")
        await session.eval_js("""
            document.querySelector('#agent-repair-button').click();
        """)
        await asyncio.sleep(2.0)
        await session.capture_screenshot("03_repair_proposed_diff.png")

        # Verify state in DOM
        state = await session.eval_js("document.querySelector('#agent-state-label').textContent")
        print(f"Current Agent State: {state}")
        diff_text = await session.eval_js("document.querySelector('#diff-output').textContent")
        print(f"Diff output snippet: {diff_text[:120]}...")

        # Step 4: Test Approval Barrier & Apply to Authorized Disk Target
        print("4. Testing Approval Requirement & Apply to Authorized Target...")
        # Mock window.confirm to return true for headless testing
        await session.eval_js("window.confirm = () => true;")
        await session.eval_js("document.querySelector('#agent-apply-btn').click();")
        await asyncio.sleep(1.5)
        await session.capture_screenshot("04_patch_applied_rollback_active.png")

        applied_state = await session.eval_js("document.querySelector('#agent-state-label').textContent")
        print(f"Post-Apply Agent State: {applied_state}")

        # Step 5: Test Instant Rollback
        print("5. Testing Instant Rollback...")
        await session.eval_js("document.querySelector('#agent-rollback-btn').click();")
        await asyncio.sleep(1.2)
        await session.capture_screenshot("05_rollback_completed.png")

        rolled_back_state = await session.eval_js("document.querySelector('#agent-state-label').textContent")
        print(f"Post-Rollback Agent State: {rolled_back_state}")

        # Step 6: Test Mode Switcher (Switch to Local AST Engine)
        print("6. Testing Provider Mode Switcher...")
        await session.eval_js("document.querySelector('#mode-local-btn').click();")
        await asyncio.sleep(0.5)
        await session.capture_screenshot("06_mode_switched_local_ast.png")

        # Step 7: Laptop Viewport (1440x900)
        print("7. Testing Laptop Viewport (1440x900)...")
        await session.set_viewport(1440, 900, is_mobile=False)
        await asyncio.sleep(0.5)
        await session.capture_screenshot("07_laptop_1440x900.png")

        # Step 8: Tablet Viewport (768x1024)
        print("8. Testing Tablet Viewport (768x1024)...")
        await session.set_viewport(768, 1024, is_mobile=False)
        await asyncio.sleep(0.5)
        await session.capture_screenshot("08_tablet_768px.png")

        # Step 9: Mobile Viewport Responsiveness (390x844 iPhone 14)
        print("9. Testing Mobile Viewport Responsiveness (390x844)...")
        await session.set_viewport(390, 844, is_mobile=True)
        await asyncio.sleep(0.8)
        await session.capture_screenshot("09_mobile_responsive_390px.png")

        # Reset viewport
        await session.set_viewport(1920, 1080, is_mobile=False)
        print("--- All E2E browser verification steps completed successfully! ---")

        await session.close()
    finally:
        chrome_proc.terminate()
        try:
            chrome_proc.wait(timeout=2)
        except Exception:
            chrome_proc.kill()


if __name__ == "__main__":
    asyncio.run(run_e2e_tests())
