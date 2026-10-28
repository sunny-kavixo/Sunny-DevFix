"""
Master Video Assembly Script for Sunny-DevFix Hackathon Final Release.
Concatenates real application scene recordings with master narration audio and subtitles.
"""

import subprocess
from pathlib import Path

FINAL_DIR = Path("release/video/final")
CLIPS_DIR = FINAL_DIR / "clips"
NARRATION_WAV = FINAL_DIR / "Sunny-DevFix-Final-Narration.wav"
SUBTITLES_SRT = FINAL_DIR / "Sunny-DevFix-Final-Subtitles.srt"
OUTPUT_MP4 = FINAL_DIR / "Sunny-DevFix-Final-Live-Demo.mp4"

SCENE_NAMES = [
    "scene1_problem",
    "scene2_product_intro",
    "scene3_live_debugging",
    "scene4_agent_reasoning",
    "scene5_patch_diff",
    "scene6_verification_rollback",
    "scene7_technical_evidence",
    "scene8_conclusion",
]


def assemble_video():
    print("--- Assembling Master Sunny-DevFix Hackathon MP4 ---")
    concat_list_file = FINAL_DIR / "clips_concat.txt"
    entries = []
    for sc in SCENE_NAMES:
        mp4_path = CLIPS_DIR / f"{sc}.mp4"
        if not mp4_path.exists():
            raise FileNotFoundError(f"Missing required clip: {mp4_path}")
        entries.append(f"file '{mp4_path.resolve()}'")

    concat_list_file.write_text("\n".join(entries))

    # Assemble using ffmpeg:
    # 1. Concat video stream at 30 fps 1920x1080
    # 2. Add narration audio as AAC 192kbps
    # 3. Embed subtitle track + burn crisp subtitles for maximum evaluator accessibility
    # 4. H.264 high profile with yuv420p and faststart
    cmd = [
        "/opt/homebrew/bin/ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", str(concat_list_file),
        "-i", str(NARRATION_WAV),
        "-vf", f"fps=30,scale=1920:1080:flags=lanczos,subtitles={SUBTITLES_SRT.resolve()}:force_style='FontName=Helvetica,FontSize=20,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BackColour=&H80000000,BorderStyle=4,MarginV=35'",
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        "-movflags", "+faststart",
        str(OUTPUT_MP4)
    ]

    print("Running FFmpeg master render...")
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print("FFmpeg stderr:\n", res.stderr[-2000:])
        raise RuntimeError("FFmpeg assembly failed")

    # Probe resulting video
    probe = subprocess.run([
        "/opt/homebrew/bin/ffprobe", "-i", str(OUTPUT_MP4),
        "-show_entries", "format=duration,size,bit_rate:stream=width,height,r_frame_rate,codec_name",
        "-v", "quiet", "-of", "json"
    ], capture_output=True, text=True, check=True)

    print("=" * 60)
    print(f"Master Video Render Complete: {OUTPUT_MP4}")
    import json
    meta = json.loads(probe.stdout)
    dur = float(meta["format"]["duration"])
    size_mb = int(meta["format"]["size"]) / (1024 * 1024)
    print(f"Duration: {dur:.2f} seconds ({int(dur // 60)}m {int(dur % 60):02d}s)")
    print(f"File Size: {size_mb:.2f} MB")
    print(f"Video Stream: {meta['streams'][0]['width']}x{meta['streams'][0]['height']} @ {meta['streams'][0]['r_frame_rate']} ({meta['streams'][0]['codec_name']})")
    print(f"Audio Stream: {meta['streams'][1]['codec_name']}")
    print("=" * 60)


if __name__ == "__main__":
    assemble_video()
