#!/usr/bin/env python3
"""Verification utility for live Nebius Token Factory & NVIDIA model inference."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sunny_devfix.providers.nebius import NebiusClient, redact_key
from sunny_devfix.providers.nvidia_repair import run_nvidia_repair

SYNTHETIC_SOURCE = """def compute_discount(price, rate):
    discount = price * rte
    return price - discount

print(compute_discount(100, 0.15))
"""

SYNTHETIC_TRACEBACK = """Traceback (most recent call last):
  File "pricing.py", line 5, in <module>
    print(compute_discount(100, 0.15))
  File "pricing.py", line 2, in compute_discount
    discount = price * rte
NameError: name 'rte' is not defined
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Test live Nebius Token Factory inference.")
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="NVIDIA model ID to evaluate (e.g. nvidia/Nemotron-3_5-Lightning or nvidia/Llama-3.1-Nemotron-70B-Instruct).",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Execute real live inference call against Nebius Token Factory (requires NEBIUS_API_KEY).",
    )
    args = parser.parse_args()

    client = NebiusClient(model=args.model)
    diagnostics = client.get_diagnostics()

    print("=" * 65)
    print("Sunny-DevFix: Nebius Token Factory Inference Diagnostic")
    print("=" * 65)
    print(f"Provider:        {diagnostics['provider']}")
    print(f"Model ID:        {diagnostics['model']}")
    print(f"Base URL:        {diagnostics['base_url']}")
    print(f"Key Configured:  {diagnostics['configured']} ({diagnostics['key_masked']})")
    print(f"Enabled:         {diagnostics['enabled']}")
    print(f"Timeout:         {diagnostics['timeout_seconds']}s")
    print("Supported NVIDIA Models on Nebius Token Factory:")
    for model_name in diagnostics.get("supported_models", []):
        print(f"  - {model_name}")
    print("=" * 65)

    if not client.is_configured:
        print("\n[STATUS: BLOCKED / AWAITING USER KEY]")
        print("NEBIUS_API_KEY environment variable is not configured.")
        print("\nTo execute a live inference test:")
        print("  1. Export your Nebius Token Factory API key:")
        print("     export NEBIUS_API_KEY=\"your-nebius-token-factory-key\"")
        print("     export DEVFIX_NEBIUS_ENABLED=\"true\"")
        print("  2. Run this script with --execute:")
        print("     python3 tools/verify_nebius_inference.py --execute")
        print("\nCost note: A single synthetic run consumes ~800 total tokens.")
        print("Estimated cost on NVIDIA Nemotron is less than $0.0002 (< 1/50th of a cent).")
        return 2

    if not args.execute:
        print("\n[KEY DETECTED — AWAITING EXPLICIT --execute APPROVAL]")
        print("The NEBIUS_API_KEY is configured in the environment.")
        print("In accordance with hackathon safety rules, no billable credits are consumed without --execute.")
        print("\nRun with --execute to authorize and perform live inference:")
        print("  python3 tools/verify_nebius_inference.py --execute")
        return 0

    print("\nExecuting live NVIDIA Nemotron repair on Nebius Token Factory...")
    started = time.monotonic()
    result = run_nvidia_repair(
        SYNTHETIC_SOURCE,
        SYNTHETIC_TRACEBACK,
        filename="pricing.py",
        client=client,
        fallback_on_error=False,
    )
    duration_ms = int((time.monotonic() - started) * 1000)

    print("\n" + "=" * 65)
    print("LIVE INFERENCE RESULT")
    print("=" * 65)
    print(f"Duration:         {duration_ms} ms")
    print(f"Provider:         {result.provider}")
    print(f"Model:            {result.model}")
    print(f"Is AI Generated:  {result.is_ai_generated}")
    print(f"Root Cause Title: {result.root_cause_title}")
    print(f"Root Cause Expl:  {result.root_cause_explanation}")
    print(f"Next Step:        {result.next_step}")
    print(f"Confidence:       {result.confidence}")
    print(f"Syntax Valid:     {result.syntax_valid}")
    print("\nUnified Diff Produced by NVIDIA Nemotron:")
    print(result.unified_diff)
    print("=" * 65)

    # Save sanitized evidence record
    record_path = Path("docs/hackathon/LIVE_INFERENCE_RECORD.json")
    evidence_record = {
        "timestamp": time.time(),
        "provider": result.provider,
        "model": result.model,
        "is_ai_generated": result.is_ai_generated,
        "duration_ms": duration_ms,
        "key_masked": redact_key(client.api_key),
        "root_cause_title": result.root_cause_title,
        "root_cause_explanation": result.root_cause_explanation,
        "next_step": result.next_step,
        "confidence": result.confidence,
        "fix_description": result.fix_description,
        "syntax_valid": result.syntax_valid,
        "unified_diff": result.unified_diff,
        "after_source": result.after_source,
    }
    record_path.write_text(json.dumps(evidence_record, indent=2), encoding="utf-8")
    print(f"\nSanitized live evidence saved to: {record_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
