# Frontier Buildathon 2026 submission checklist

Track: **Developer Tools & Open Source**

## Repository readiness

- [x] Public-repository-ready Git history with focused commits
- [x] Pinned Python runtime in `.python-version`
- [x] Runtime and development lockfiles
- [x] Dockerfile and `.dockerignore`
- [x] `.env.example` without secrets
- [x] MIT license
- [x] README with setup, run, test, Docker, safety, and limitations
- [x] One offline test command: `make test`
- [x] No project files use machine-specific absolute paths

## Verification evidence

Run these from the repository before submitting:

```bash
make test
  --tmpfs /tmp:rw,nosuid,nodev,size=64m \
  sunny-devfix:local make test
```

Record the actual test count and Docker result in the submission notes. Do not
copy a previous run's number after the suite changes.

## Required event actions outside this repository

- [ ] Join the Buildathon dashboard before the registration cutoff
- [ ] Use the connected GitHub account for the public repository
- [ ] Select **Developer Tools & Open Source**
- [ ] Add qualifying OmniRush sessions in the Buildathon dashboard
- [ ] Add the public repository URL
- [ ] Record a 2–3 minute demo using `docs/demo-script.md`
- [ ] Add a live link if deployed
- [ ] Copy the OmniRush Submission ID into Unstop
- [ ] Submit before **20 Oct 2026, 11:59 PM IST**

The agent cannot complete the public push, account registration, dashboard
session acceptance, or Unstop submission without the owner's credentials and
explicit public-action approval.
