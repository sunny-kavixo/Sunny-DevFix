"""
Narration and Subtitle Generator for Sunny-DevFix Hackathon Demo.
Uses high-quality macOS natural voice 'Daniel' (English UK) with calibrated pacing.
"""

import subprocess
from pathlib import Path
import json

FINAL_DIR = Path("release/video/final")
FINAL_DIR.mkdir(parents=True, exist_ok=True)
TEMP_DIR = FINAL_DIR / "temp_audio"
TEMP_DIR.mkdir(parents=True, exist_ok=True)

VOICE = "Daniel"
RATE = "165"  # Calibrated words per minute for warm, authoritative delivery

SCENES = [
    {
        "id": "scene1",
        "title": "Problem Statement",
        "text": "Every software team has faced this crisis: a runtime exception strikes production, causing silent corruption and broken transactions. Standard AI coding assistants jump straight to rewriting entire files, hallucinating unseen APIs and introducing fatal regressions. Today, we need a smarter, safer way to debug Python.",
        "target_sec": 23.0
    },
    {
        "id": "scene2",
        "title": "Product Introduction",
        "text": "Meet Sunny DevFix: an autonomous, causal Python debugging agent purpose-built for the Nebius and NVIDIA Hackathon. Re-architected with a professional developer workspace, Sunny DevFix pairs NVIDIA Nemotron on Nebius Token Factory with local deterministic AST guardrails, a cryptographic human approval barrier, and isolated container verification.",
        "target_sec": 24.0
    },
    {
        "id": "scene3",
        "title": "Live Debugging Intake",
        "text": "Let's inspect a live billing failure. In the workspace panel, we load a defective source file with a subtle typo in a billing calculation, alongside its raw traceback. Notice the Live Code Guardian beneath the editor: it performs real-time AST linting as you type. It flags unmapped identifiers immediately, without executing untrusted code.",
        "target_sec": 24.0
    },
    {
        "id": "scene4",
        "title": "Agent Reasoning & Repair",
        "text": "Now, we engage the autonomous repair engine. With one click, Sunny DevFix dispatches the problem context to NVIDIA Nemotron on Nebius Token Factory. The agent state machine advances in real time: analyzing the traceback, mapping deepest call frames, and synthesizing a pinpoint repair. The causal engine explains exactly why the failure occurred.",
        "target_sec": 25.0
    },
    {
        "id": "scene5",
        "title": "Patch Inspection & Approval",
        "text": "Before a single byte touches disk, Sunny DevFix requires explicit human authorization. The diff studio presents an exact side-by-side comparison and color-coded unified diff. Only the defective variable is corrected, preserving existing syntax. A one-time cryptographic approval token ensures no autonomous agent writes to your workspace without your consent.",
        "target_sec": 25.0
    },
    {
        "id": "scene6",
        "title": "Container Verification & Rollback",
        "text": "Once approved, the patch is verified in an isolated Docker sandbox with zero network access, read-only filesystem, and memory limits. Exit codes and stdout are verified before and after. If anything is unexpected, our instant rollback token restores the exact pre-patch code in milliseconds.",
        "target_sec": 21.0
    },
    {
        "id": "scene7",
        "title": "Technical Evidence & Tests",
        "text": "Sunny DevFix is thoroughly verified. Our comprehensive test suite covers eighty passing unit and integration tests in under one second, with a median benchmark latency of zero point one eight milliseconds. A self-contained test bundle is ready for evaluator testing.",
        "target_sec": 18.0
    },
    {
        "id": "scene8",
        "title": "Conclusion",
        "text": "Sunny DevFix: NVIDIA-Powered Verified Code Repair. Open source under the MIT License on GitHub.",
        "target_sec": 10.0
    }
]


def format_srt_time(seconds: float) -> str:
    millis = int((seconds % 1) * 1000)
    total_seconds = int(seconds)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def generate_audio_and_subtitles():
    concat_list = []
    srt_entries = []
    current_time = 0.0

    print("--- Synthesizing Narration with voice 'Daniel' ---")
    for idx, sc in enumerate(SCENES, start=1):
        aiff_path = TEMP_DIR / f"{sc['id']}.aiff"
        wav_path = TEMP_DIR / f"{sc['id']}.wav"
        padded_wav = TEMP_DIR / f"{sc['id']}_padded.wav"

        # 1. Synthesize via macOS say
        subprocess.run(["say", "-v", VOICE, "-r", RATE, "-o", str(aiff_path), sc["text"]], check=True)

        # 2. Convert to 48kHz mono 16-bit WAV
        subprocess.run([
            "/opt/homebrew/bin/ffmpeg", "-y", "-i", str(aiff_path),
            "-ar", "48000", "-ac", "1", "-c:a", "pcm_s16le", str(wav_path)
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

        # 3. Check natural audio duration
        probe = subprocess.run([
            "/opt/homebrew/bin/ffprobe", "-i", str(wav_path),
            "-show_entries", "format=duration", "-v", "quiet", "-of", "csv=p=0"
        ], capture_output=True, text=True, check=True)
        raw_dur = float(probe.stdout.strip())
        target_dur = sc["target_sec"]
        print(f"[{sc['id']}] {sc['title']}: Raw audio = {raw_dur:.2f}s, Target = {target_dur:.1f}s")

        # 4. Pad or adjust so clip matches target duration exactly
        if raw_dur < target_dur:
            pad_needed = target_dur - raw_dur
            subprocess.run([
                "/opt/homebrew/bin/ffmpeg", "-y", "-i", str(wav_path),
                "-af", f"apad=pad_dur={pad_needed}",
                str(padded_wav)
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        else:
            # Subtle atempo speed adjustment if raw duration exceeds target slightly
            speed = raw_dur / target_dur
            subprocess.run([
                "/opt/homebrew/bin/ffmpeg", "-y", "-i", str(wav_path),
                "-af", f"atempo={speed:.4f}",
                str(padded_wav)
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

        concat_list.append(f"file '{padded_wav.resolve()}'")

        # Add SRT entry
        start_srt = format_srt_time(current_time)
        end_srt = format_srt_time(current_time + target_dur - 0.2)
        srt_entries.append(f"{idx}\n{start_srt} --> {end_srt}\n{sc['text']}\n")
        current_time += target_dur

    # Write concat file
    concat_file = TEMP_DIR / "concat_list.txt"
    concat_file.write_text("\n".join(concat_list))

    # Master narration WAV
    final_wav = FINAL_DIR / "Sunny-DevFix-Final-Narration.wav"
    subprocess.run([
        "/opt/homebrew/bin/ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", str(concat_file), "-c", "copy", str(final_wav)
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    # Write Master Subtitles SRT
    final_srt = FINAL_DIR / "Sunny-DevFix-Final-Subtitles.srt"
    final_srt.write_text("\n".join(srt_entries))

    # Probe total final narration duration
    probe = subprocess.run([
        "/opt/homebrew/bin/ffprobe", "-i", str(final_wav),
        "-show_entries", "format=duration", "-v", "quiet", "-of", "csv=p=0"
    ], capture_output=True, text=True, check=True)
    total_dur = float(probe.stdout.strip())
    mins = int(total_dur // 60)
    secs = int(total_dur % 60)

    print("=" * 60)
    print(f"Generated Master Narration: {final_wav} ({total_dur:.2f}s -> {mins}m {secs:02d}s)")
    print(f"Generated Master Subtitles: {final_srt} ({len(SCENES)} subtitles)")
    print("=" * 60)
    return total_dur


if __name__ == "__main__":
    generate_audio_and_subtitles()
