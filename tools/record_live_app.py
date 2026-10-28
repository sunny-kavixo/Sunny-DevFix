"""
Real Interactive Application Screen Recording Generator for Sunny-DevFix.
Automates Google Chrome over DevTools Protocol (CDP) to perform real typing,
clicking, hovering, and state transitions, capturing high-resolution 1920x1080 frames.
"""

import asyncio
import base64
import json
import os
import subprocess
import time
from pathlib import Path
import httpx
import websockets

CHROME_PATH = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
CHROME_PORT = 9222
BASE_URL = "http://127.0.0.1:8000"

RECORDINGS_DIR = Path("release/video/final/clips")
RECORDINGS_DIR.mkdir(parents=True, exist_ok=True)


class BrowserRecorder:
    def __init__(self, ws_url: str):
        self.ws_url = ws_url
        self.ws = None
        self.msg_id = 0

    async def connect(self):
        self.ws = await websockets.connect(self.ws_url, max_size=50_000_000)

    async def send(self, method: str, params: dict = None) -> dict:
        self.msg_id += 1
        payload = {"id": self.msg_id, "method": method, "params": params or {}}
        await self.ws.send(json.dumps(payload))
        while True:
            resp_raw = await self.ws.recv()
            resp = json.loads(resp_raw)
            if resp.get("id") == self.msg_id:
                return resp.get("result", {})

    async def eval_js(self, expression: str):
        res = await self.send("Runtime.evaluate", {
            "expression": expression,
            "returnByValue": True,
            "awaitPromise": True
        })
        return res.get("result", {}).get("value")

    async def capture_frame(self, path: Path):
        res = await self.send("Page.captureScreenshot", {"format": "jpeg", "quality": 95})
        data = base64.b64decode(res["data"])
        path.write_bytes(data)

    async def record_scene(self, scene_name: str, duration_sec: float, fps: int = 15, actions: list = None):
        scene_dir = RECORDINGS_DIR / scene_name
        scene_dir.mkdir(parents=True, exist_ok=True)
        total_frames = int(duration_sec * fps)
        interval = 1.0 / fps

        action_idx = 0
        actions = actions or []

        print(f"Recording {scene_name}: {duration_sec:.1f}s ({total_frames} frames at {fps} fps)...")
        start_time = time.time()
        for frame_num in range(total_frames):
            frame_time = frame_num / fps
            # Execute scheduled action if current time >= action timestamp
            while action_idx < len(actions) and frame_time >= actions[action_idx]["time"]:
                act = actions[action_idx]
                if "js" in act:
                    await self.eval_js(act["js"])
                elif "action" in act:
                    act["action"]()
                action_idx += 1

            frame_path = scene_dir / f"frame_{frame_num:05d}.jpg"
            await self.capture_frame(frame_path)
            elapsed = time.time() - start_time
            expected = (frame_num + 1) * interval
            to_sleep = expected - elapsed
            if to_sleep > 0:
                await asyncio.sleep(to_sleep)

        print(f"Finished {scene_name} in {time.time() - start_time:.1f}s.")
        # Compile clip with ffmpeg
        clip_mp4 = RECORDINGS_DIR / f"{scene_name}.mp4"
        cmd = [
            "/opt/homebrew/bin/ffmpeg", "-y",
            "-framerate", str(fps),
            "-i", str(scene_dir / "frame_%05d.jpg"),
            "-vf", "scale=1920:1080:flags=lanczos",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-crf", "18",
            str(clip_mp4)
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        print(f"Compiled clip: {clip_mp4}")
        return clip_mp4


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


async def record_all_scenes():
    chrome_proc = launch_chrome()
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.put(f"http://127.0.0.1:{CHROME_PORT}/json/new")
            page_info = resp.json()
            ws_url = page_info["webSocketDebuggerUrl"]

        recorder = BrowserRecorder(ws_url)
        await recorder.connect()
        await recorder.send("Page.enable")
        await recorder.send("Runtime.enable")
        await recorder.send("Page.navigate", {"url": BASE_URL})
        await asyncio.sleep(1.0)
        await recorder.eval_js("window.confirm = () => true;")

        # Scene 1: Problem Overview (23s)
        # Shows defective source and traceback in billing.py
        await recorder.record_scene("scene1_problem", 23.0, fps=12, actions=[
            {"time": 0.5, "js": "document.querySelector('#example-select').value='name_error';document.querySelector('#load-demo').click();"},
            {"time": 4.0, "js": "document.querySelector('#source-input').focus();"},
            {"time": 10.0, "js": "document.querySelector('#traceback-input').focus();"},
        ])

        # Scene 2: Product Architecture & IDE Workspace (24s)
        # Overview of the 3-column AI developer workspace layout & mode switcher
        await recorder.record_scene("scene2_product_intro", 24.0, fps=12, actions=[
            {"time": 2.0, "js": "document.querySelector('#mode-nvidia-btn').classList.add('pulse-glow');"},
            {"time": 7.0, "js": "document.querySelector('#mode-local-btn').click();"},
            {"time": 13.0, "js": "document.querySelector('#mode-nvidia-btn').click();"},
            {"time": 18.0, "js": "document.querySelector('#guardian-strip').scrollIntoView({behavior: 'smooth'});"},
        ])

        # Scene 3: Live Debugging Intake & Live Code Guardian (24s)
        # Interacting with the editor, live AST diagnostics, typing, switching examples
        await recorder.record_scene("scene3_live_debugging", 24.0, fps=12, actions=[
            {"time": 1.0, "js": "document.querySelector('#example-select').value='syntax_error';document.querySelector('#load-demo').click();"},
            {"time": 8.0, "js": "document.querySelector('#example-select').value='zero_div';document.querySelector('#load-demo').click();"},
            {"time": 15.0, "js": "document.querySelector('#example-select').value='name_error';document.querySelector('#load-demo').click();"},
            {"time": 20.0, "js": "document.querySelector('#source-input').focus();"},
        ])

        # Scene 4: Agent Reasoning & Repair Synthesis (25s)
        # Clicking AI Repair, watching the stepper advance, inspecting root-cause explanation
        await recorder.record_scene("scene4_agent_reasoning", 25.0, fps=12, actions=[
            {"time": 1.5, "js": "document.querySelector('#agent-repair-button').click();"},
            {"time": 8.0, "js": "document.querySelector('.diagnostic-card').scrollIntoView({behavior: 'smooth'});"},
            {"time": 15.0, "js": "document.querySelector('.stepper-vertical').scrollIntoView({behavior: 'smooth'});"},
            {"time": 20.0, "js": "document.querySelector('.comparison-grid').scrollIntoView({behavior: 'smooth'});"},
        ])

        # Scene 5: Patch Inspection & Approval Barrier (25s)
        # Side-by-side Before/After, Unified diff, copy buttons, and human authorization gate
        await recorder.record_scene("scene5_patch_diff", 25.0, fps=12, actions=[
            {"time": 2.0, "js": "document.querySelector('#diff-output').scrollIntoView({behavior: 'smooth'});"},
            {"time": 8.0, "js": "document.querySelector('#copy-diff').click();"},
            {"time": 13.0, "js": "document.querySelector('#authorization-box').scrollIntoView({behavior: 'smooth'});"},
            {"time": 19.0, "js": "document.querySelector('#agent-apply-btn').click();"},
        ])

        # Scene 6: Isolated Container Verification & Rollback (21s)
        # Docker sandbox scorecard, execution logs, and instant one-click rollback
        await recorder.record_scene("scene6_verification_rollback", 21.0, fps=12, actions=[
            {"time": 2.0, "js": "document.querySelector('#verify-evidence').click();"},
            {"time": 11.0, "js": "document.querySelector('#agent-rollback-btn').click();"},
            {"time": 16.0, "js": "document.querySelector('.safety-card').scrollIntoView({behavior: 'smooth'});"},
        ])

        # Scene 7: Technical Evidence & Test Suite (18s)
        # Demonstrating the 80/80 test suite in terminal & benchmark evidence
        await recorder.record_scene("scene7_technical_evidence", 18.0, fps=12, actions=[
            {"time": 1.0, "js": "document.querySelector('.app-footer').scrollIntoView({behavior: 'smooth'});"},
            {"time": 8.0, "js": "document.querySelector('.topbar').scrollIntoView({behavior: 'smooth'});"},
        ])

        # Scene 8: Conclusion & Open Source Repository (10s)
        # Summary & GitHub repository badge
        await recorder.record_scene("scene8_conclusion", 10.0, fps=12, actions=[
            {"time": 0.5, "js": "window.scrollTo(0, 0);"},
        ])

        print("All scenes recorded and compiled into MP4 clips successfully!")
    finally:
        chrome_proc.terminate()
        try:
            chrome_proc.wait(timeout=2)
        except Exception:
            chrome_proc.kill()


if __name__ == "__main__":
    asyncio.run(record_all_scenes())
