# Sunny-DevFix: Final Devpost Submission Handoff

**Hackathon:** Nebius × NVIDIA Global AI Hackathon 2026  
**Track:** Coding and Agentic Engineering  
**Official Deadline:** October 30, 2026 at 10:30 PM IST (10:00 AM PDT)  
**Submission Portal:** [https://nebiusglobalaihackathon.devpost.com/](https://nebiusglobalaihackathon.devpost.com/)  

---

## 1. Ready-to-Paste Devpost Form Fields

### Project Title
`Sunny-DevFix — NVIDIA-Powered Verified Code Repair`

### Tagline (under 200 characters)
`Autonomous Python traceback debugging and verified patch repair powered by NVIDIA Nemotron on Nebius Token Factory with human-in-the-loop safety and isolated Docker verification.`

### Track
`Coding and Agentic Engineering`

### GitHub Repository URL
`https://github.com/sunny-kavixo/Sunny-DevFix`

### Release / Test Build URL
`https://github.com/sunny-kavixo/Sunny-DevFix/releases/tag/v0.2.0`

### License
`MIT License`

---

## 2. Devpost Long-Form Description (Markdown)

```markdown
### Inspiration
Python developers waste hours tracing complex stack traces, identifying broken variable references, and validating fixes. While LLMs can suggest code, naive code assistants often hallucinate invalid syntax, break unrelated logic, or overwrite files without review.

We built **Sunny-DevFix** to transform Python runtime debugging into an accountable, verified agentic workflow. By combining **NVIDIA Nemotron causal reasoning on Nebius Token Factory** with deterministic AST analysis, token-bound human approval gates, and disposable Docker container sandboxes, Sunny-DevFix diagnoses the defect, synthesizes a minimal surgical repair, displays a side-by-side unified diff, and verifies the fix before applying it to disk.

### What it does
Sunny-DevFix operates a 6-stage agentic workflow:
1. **ANALYZED**: Parses raw Python tracebacks, extracts chained frames, and maps the deepest failing frame to the exact line and scope in the source code without importing or running untrusted code on the host.
2. **PATCH_PROPOSED**: Transmits bounded context to `nvidia/Nemotron-3_5-Lightning` via Nebius Token Factory. The model diagnoses the causal root cause and synthesizes a structured repair adhering to a strict Pydantic JSON schema.
3. **AWAITING_APPROVAL**: Validates that the proposed code compiles syntactically and renders an interactive side-by-side unified diff. A 5-minute single-use cryptographic approval token is issued.
4. **APPLIED**: The human operator must explicitly click **Approve & Apply**. The patch is written atomically to disk and immediately armed with a single-use rollback token.
5. **TESTING**: Optionally launches twin disposable Docker containers (`--network none`, `--read-only`, 128MB RAM limit) to execute before-and-after reproductions in parallel.
6. **VERIFIED / ROLLED_BACK**: The evidence scorecard reports syntax validity, reproduction success, and regression detection. If regressions occur, clicking **Instant Rollback** immediately restores exact pre-patch bytes.

### How we built it
- **AI Reasoning**: NVIDIA Nemotron on Nebius Token Factory (`nvidia/Nemotron-3_5-Lightning`).
- **Backend & State Machine**: FastAPI, Pydantic v2, Python 3.14 AST standard library.
- **Security Boundary**: Thread-safe cryptographic approval tokens, path traversal prevention, symlink escape rejection, and passive data handling.
- **Frontend**: Zero-framework Vanilla HTML5/CSS3/JavaScript devtool UI featuring an interactive 6-step agent stepper, live model badge, and debounced Live Code Guardian linter.
- **Sandbox**: Hardened Docker runner with non-root UID `65532:65532`, dropped Linux capabilities, and zero network access.

### Challenges we ran into
- Ensuring large exception messages from upstream APIs never leak credentials into logs or client responses (resolved with automated Bearer/token sanitization regexes).
- Building an agentic workflow that guarantees zero unauthorized disk writes while maintaining sub-millisecond local parsing speed.
- Designing a responsive, Linear/Vercel-grade 2-column developer workspace that displays large code blocks and diffs comfortably without clutter.

### Accomplishments that we're proud of
- **Live Authenticated Inference Verified**: Successfully executed genuine live inference using `nvidia/Nemotron-3_5-Lightning` on Nebius Token Factory, resolving NameErrors in 7.506 seconds.
- **Sub-Millisecond Local Analysis**: Median local AST diagnosis latency is **0.18 ms** with only **95 KiB** peak traced memory.
- **Exhaustive Test Coverage**: **86 automated unit, integration, and adversarial security tests passing cleanly** in under 1 second.
- **Browser CDP Verification**: Automated end-to-end browser test suite passing across desktop, laptop, tablet, and mobile viewports.
- **Clean Standalone Build**: 3.0 MB self-contained judge package runnable 100% offline with reproducible deterministic fallback.

### What we learned
NVIDIA Nemotron displays exceptional causal reasoning over complex Python call stacks, correctly identifying variable scoping mismatches and instruction-following JSON output formats.

### What's next for Sunny-DevFix
- Expanding multi-file repository-level workspace refactoring.
- Native VS Code language server protocol (LSP) integration.
- Automated test generation for synthesized patches.
```

---

## 3. Only Remaining Owner Actions

1. **Video Demonstration (Owner Responsibility):**
   - Record and edit the product demonstration video (2–3 minutes).
   - Upload to YouTube as **Public** or **Unlisted**.
   - Copy the YouTube video URL.
2. **Submit on Devpost:**
   - Log in to [https://nebiusglobalaihackathon.devpost.com/](https://nebiusglobalaihackathon.devpost.com/).
   - Paste the fields above.
   - Paste your YouTube video link.
   - Review and click **Submit**.
