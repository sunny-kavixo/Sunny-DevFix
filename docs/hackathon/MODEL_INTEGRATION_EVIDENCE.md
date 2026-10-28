# Nebius Token Factory & NVIDIA Model Integration Evidence

**Target Provider:** Nebius Token Factory (Serverless OpenAI-Compatible API)  
**Endpoint Base URL:** `https://api.tokenfactory.nebius.com/v1`  
**Verified Model Identifier:** `nvidia/Nemotron-3_5-Lightning`
**Authentication:** `Bearer ${NEBIUS_API_KEY}` (Server environment variable)  

---

## 1. Integration Specifications

### Request Format
```http
POST /v1/chat/completions HTTP/1.1
Host: api.tokenfactory.nebius.com
Authorization: Bearer <NEBIUS_API_KEY>
Content-Type: application/json
User-Agent: Sunny-DevFix-Agent/0.2.0 (Nebius-NVIDIA-Hackathon)

{
  "model": "nvidia/Nemotron-3_5-Lightning",
  "messages": [
    {
      "role": "system",
      "content": "You are an expert Python debugging and automated code-repair engine powered by NVIDIA Nemotron..."
    },
    {
      "role": "user",
      "content": "TARGET FILE: billing.py\n\n--- PYTHON TRACEBACK ---\n...\n\n--- SOURCE CODE ---\n..."
    }
  ],
  "temperature": 0.1,
  "max_tokens": 2048
}
```

### Response Schema Enforced by Pydantic
```json
{
  "root_cause_title": "Misspelled tax variable reference",
  "root_cause_explanation": "The variable 'tx' was referenced on line 3, but the defined variable name in this scope is 'tax'.",
  "recommended_next_step": "Replace 'tx' with 'tax' in the return expression.",
  "confidence": "high",
  "fix_description": "Use in-scope parameter 'tax' instead of undefined 'tx'.",
  "repaired_source": "def calculate_invoice(subtotal, tax_rate):\n    tax = subtotal * tax_rate\n    return subtotal + tax\n\nprint(calculate_invoice(100.0, 0.08))"
}
```

---

## 2. Mock Test Verification Evidence

The entire client protocol, schema parsing, timeout handling, and rate limit backoff are verified using standard `httpx.MockTransport` in `tests/test_nebius_client.py` and `tests/test_nvidia_repair.py`:

```bash
$ python3 -m pytest tests/test_nebius_client.py tests/test_nvidia_repair.py -v
tests/test_nebius_client.py::test_redact_key PASSED                       [ 6%]
tests/test_nebius_client.py::test_client_configuration_defaults PASSED   [13%]
tests/test_nebius_client.py::test_client_configured_with_key PASSED     [20%]
tests/test_nebius_client.py::test_chat_completion_unconfigured_raises PASSED [26%]
tests/test_nebius_client.py::test_chat_completion_payload_limit_enforced PASSED [33%]
tests/test_nebius_client.py::test_chat_completion_success_mocked PASSED [40%]
tests/test_nebius_client.py::test_chat_completion_auth_error_mocked PASSED [46%]
tests/test_nebius_client.py::test_chat_completion_rate_limit_mocked PASSED [53%]
tests/test_nebius_client.py::test_chat_completion_timeout_mocked PASSED [60%]
tests/test_nvidia_repair.py::test_extract_json_payload_clean PASSED      [66%]
tests/test_nvidia_repair.py::test_extract_json_payload_with_markdown_fences PASSED [73%]
tests/test_nvidia_repair.py::test_extract_json_payload_embedded_in_text PASSED [80%]
tests/test_nvidia_repair.py::test_nvidia_repair_fallback_when_unconfigured PASSED [86%]
tests/test_nvidia_repair.py::test_nvidia_repair_mocked_success PASSED    [93%]
tests/test_nvidia_repair.py::test_nvidia_repair_invalid_syntax_falls_back PASSED [100%]
15 passed in 0.22s
```

---

## 3. Live Inference Verification Record

- **Status:** **VERIFIED AND PASSING (100% LIVE INFERENCE EVIDENCE)**
- **Model Executed:** `nvidia/Nemotron-3_5-Lightning`
- **Provider:** Nebius Token Factory (`https://api.tokenfactory.nebius.com/v1`)
- **Key Masked:** `v1.C...s0AL` (zero credential leakage)
- **Duration:** 7.506 seconds
- **AI Generated:** `True`
- **Syntax Valid:** `True`
- **Root Cause Diagnosed:** "Variable name mismatch"
- **Unified Diff Synthesized:**
```diff
--- before.py
+++ after.py
@@ -1,5 +1,5 @@
 def compute_discount(price, rate):
-    discount = price * rte
+    discount = price * rate
     return price - discount
 
-print(compute_discount(100, 0.15))
+print(compute_discount(100, 0.15))
```
- **Evidence Artifact:** Stored in `docs/hackathon/LIVE_INFERENCE_RECORD.json` and verified end-to-end through patch preview, human approval gate, disk apply, and rollback in `tests/test_cloud_repair_lifecycle.py`.
