# Sunny-DevFix: Deployment & Judge Accessibility Guide

**Target Event:** Nebius × NVIDIA Global AI Hackathon 2026  
**Track:** Coding and Agentic Engineering  
**Submission Requirement:** Publicly accessible working demo, hosted application, or independently verifiable test build maintained through the judging period (December 15, 2026).  

---

## 1. Judge Access Strategy

To satisfy the hackathon requirement of remote judge evaluation without risking uncontrolled API spend or leaking private credentials:

### Evaluation Tiers:
1. **Tier 1 (Instant Local Test Build — Zero Key Required)**:
   - Evaluators clone the repository and run `make run` or `docker run`.
   - The application functions 100% offline using the built-in deterministic AST engine and simulated bug fixtures.
   - Evaluators can test the complete agent lifecycle, side-by-side diffs, human approval gates, and rollback mechanisms.
2. **Tier 2 (BYOK Mode — Bring Your Own Key)**:
   - Evaluators export their own `NEBIUS_API_KEY` in their local shell.
   - The app dynamically detects the credential on launch, updates the status badge to `● NVIDIA Nemotron · Nebius Token Factory`, and routes requests directly to Nebius Token Factory.
3. **Tier 3 (Hosted Cloud Deployment on Cloud Run / Fly.io)**:
   - Containerized deployment running the FastAPI service.
   - Guarded by server-side rate limits (max 5 requests per minute per IP) and daily quota caps to protect hackathon API credits from public abuse.

---

## 2. Option A: Reproducible Docker Build (Recommended for Judges)

The repository provides a single, deterministic, zero-dependency Docker build that runs on any machine with Docker:

```bash
# 1. Build the lightweight image
docker build -t sunny-devfix:latest .

# 2. Run the container (offline mode)
docker run -p 8000:8000 --rm sunny-devfix:latest

# 3. Or run with Nebius Token Factory active
docker run -p 8000:8000 --rm \
  -e NEBIUS_API_KEY="your-nebius-key" \
  -e DEVFIX_NEBIUS_ENABLED="true" \
  sunny-devfix:latest
```
Visit `http://localhost:8000`.

---

## 3. Option B: Serverless Cloud Deployment (Google Cloud Run / Fly.io)

### Cost & Resource Estimation
- **Hosting Tier**: Google Cloud Run (Free Tier: 2 million requests/month, 360,000 vCPU-seconds) or Fly.io free tier.
- **Estimated Hosting Cost**: **$0.00 / month** (well within free tier).
- **Nebius Token Factory Inference Cost**: Usage is billed according to the current Token Factory pricing for `nvidia/Nemotron-3_5-Lightning`; check the provider console before enabling judge traffic. No fixed cost claim is embedded in this release.
- **Approval Gate**: Cloud deployment requires owner approval before creating external cloud resources.

### Cloud Run Deployment Steps (Upon Approval):
```bash
# Authenticate and set project
gcloud auth login
gcloud config set project <PROJECT_ID>

# Build and submit container image to Artifact Registry
gcloud builds submit --tag gcr.io/<PROJECT_ID>/sunny-devfix:latest

# Deploy to Cloud Run with unauthenticated access enabled for judges
gcloud run deploy sunny-devfix \
  --image gcr.io/<PROJECT_ID>/sunny-devfix:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars DEVFIX_NEBIUS_ENABLED=true \
  --set-secrets NEBIUS_API_KEY=nebius-api-key:latest \
  --memory 512Mi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 2
```

---

## 4. API Abuse Prevention & Quota Safeguards

To prevent public denial of wallet or rate exhaustion:
1. **Character Caps**: Source and traceback inputs strictly capped at 20,000 bytes.
2. **Token Output Cap**: Max generation tokens capped at 2,048 tokens per repair request.
3. **No Execution on Host**: Repaired code runs only in ephemeral containers or in memory; zero compute exhaustion on the host server.
4. **Maintenance Commitment**: If hosted, the service will remain live and monitored through **December 15, 2026** (end of judging).
