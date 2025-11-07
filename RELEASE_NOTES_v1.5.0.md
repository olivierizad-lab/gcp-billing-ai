# Release v1.5.0

## Highlights
- **Automated metrics pipeline** – Cloud Run Job now clones the repository with a GitHub PAT, computes analytics, and stores snapshots in Firestore.
- **Snapshot-backed dashboard** – `/metrics` serves cached results; the UI can trigger refreshes, poll for completion, and displays up-to-date stats without hammering git.
- **Operational tooling + docs** – Makefile shortcuts simplify deploying/running the job, and documentation has been refreshed for the new workflow and version banner.

## Details

### Metrics Automation
- Added `metrics_job.py` which clones the repo, generates metrics for multiple windows, and writes snapshots to Firestore.
- `/metrics/refresh` endpoint and frontend integration allow manual refreshes directly from the dashboard.
- Metrics now load with JWT auth headers and surface clearer error states when snapshots are not ready.

### Frontend & UX
- Metrics dashboard polls for fresh snapshots, shows progress, and is scrollable on smaller viewports.
- Help modal and documentation index updated to display version `v1.5.0`.

### Tooling
- New Makefile targets: `deploy-metrics-job` and `run-metrics-job` for Cloud Run Job management.
- Deployment guide documents PAT storage in Secret Manager, scheduler setup, and manual triggers.

## Installation
The quickest way to redeploy the stack:

```bash
make deploy-web-simple PROJECT_ID=your-project-id REGION=us-central1
```

After deploying, seed the metrics snapshot:

```bash
make deploy-metrics-job PROJECT_ID=your-project-id REGION=us-central1 METRICS_SECRET=github-pat
make run-metrics-job PROJECT_ID=your-project-id REGION=us-central1 METRICS_SECRET=github-pat
```

Full documentation: https://olivierizad-lab.github.io/gcp-billing-ai/


