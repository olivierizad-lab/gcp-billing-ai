# Development Metrics & AI-Assisted Coding Analysis

> **Snapshot date:** November 7, 2025 (analysis window: last 60 calendar days)

This report mirrors the Provisioner-style metrics document. It summarises how fast we are shipping, where code is growing, and where vibe coding (AI-assisted development) is—or is not—being used today.

---

## Executive Summary

| Metric | Value |
| --- | --- |
| **Project** | GCP Billing Agent (Agent Engine UI + API) |
| **Analysis Period** | October 30, 2025 → November 7, 2025 (7 active coding days captured) |
| **Total Commits** | 125 (≈13.9 commits/day) |
| **Primary Contributors** | Mick Miller (107), olivierizad-lab (18), supporting contributors (3) |
| **Executable LOC** | 17,230 lines (19,107 including docs and assets) |
| **Release Tags** | v0.2.0-rc1, v1.3.0-rc2, v1.4.0-rc3 |
| **AI-flagged Commits** | 0 (vibe markers not yet applied) |

Key takeaways:

- The team moved from concept to an authenticated Cloud Run deployment in under two weeks.
- Documentation-first culture: ~36% of lines live in `docs/`, providing playbooks for operations and onboarding.
- Commit velocity consistently above 10 commits/day despite a single primary engineer, confirming rapid iteration.

---

## Cycle Time & Milestones

| Date | Milestone |
| --- | --- |
| Oct 30 | Repository bootstrap, Cloud Run skeleton |
| Nov 1–4 | GitBook → Jekyll migration, documentation index fixes |
| Nov 2–3 | Provisioner-style help modal & About/Implementation tabs |
| Nov 5–7 | Metrics collector, `/metrics` API, dashboard wiring |
| Nov 7 | Tagged `v1.4.0-rc3` (metrics endpoint + doc cleanup) |

Average latency from feature request to production: **< 48 hours** during this iteration.

---

## Code Volume Breakdown

| Layer | Executable LOC | Share | Notes |
| --- | ---:| ---:| --- |
| Frontend (React + CSS) | 3,351 | 19.4% | Help modal, metrics page, auth screens |
| Backend (FastAPI) | 1,565 | 9.1% | Agent discovery, auth, metrics endpoint |
| Agents (Vertex AI tooling) | 2,533 | 14.7% | ADK scripts, tool configs |
| Deployment Scripts | 2,377 | 13.8% | `web/deploy`, Cloud Build configs, Makefile targets |
| Automation Scripts | 1,253 | 7.3% | Metrics collectors, cleanup helpers |
| Documentation & Assets | 6,151 | 35.7% | Markdown guides, CSS for docs, favicon assets |
| **Total** | **17,230** | **100%** | Executable lines counted via `metrics.py` |

Backend + Frontend together account for ~28% of the codebase, while documentation retains parity with the code, ensuring institutional knowledge is captured.

---

## Productivity & Commit Metrics

| KPI | Value |
| --- | --- |
| Commits analysed | 125 |
| Average files per commit | 3.26 |
| Average line changes per commit | 303 lines |
| Total lines added | 32,212 |
| Total lines removed | 5,624 |
| Net new lines | 26,588 |

**Contributor split**

- Mick Miller – 107 commits (lead developer)
- olivierizad-lab – 18 commits (documentation, deployment workflows)
- Additional supporting contributors – 3 commits combined

**Vibe coding adoption**

- No commits yet tagged with the standard vibe markers (`Co-authored-by: vibe coding`, `AI-Author: vibe`, `#vibe`).
- ACTION: begin tagging AI-assisted commits so the dashboard can chart AI vs human contributions.

---

## Deployment & Release Metrics

- **Cloud Run Deployments:** Rolling deployments triggered via `make deploy-web-simple` or `web/deploy/deploy-web.sh`.
- **Tags:** Three release candidates to date (`v0.2.0-rc1`, `v1.3.0-rc2`, `v1.4.0-rc3`).
- **Downtime:** None reported (all Cloud Run updates rolling).
- **Hotfix turn-around:** Typically < 24 hours (example: documentation index corrections).

Next step: emit deployment metadata (tag, timestamp) from GitHub Actions into the metrics payload for release-frequency charts.

---

## Quality & Testing Snapshot

- Backend unit tests exist (`tests/test_agents.py`, 122 LOC) but broader coverage is still on the roadmap.
- Frontend currently relies on manual QA; no Jest/Vitest suite yet.
- Recommendation: expand pytest suites for FastAPI endpoints and add smoke tests for key React flows (auth, query, metrics).

---

## Using the Interactive Dashboard

1. Sign in to the web UI.
2. Open **Help → Metrics** (new tab) or browse directly to `/metrics`.
3. Select the analysis window (7, 30, 90, 180, 365 days) and press **Refresh**.
4. Export the JSON via `curl https://<api>/metrics?days=30` for offline analysis.

The dashboard surfaces:
- KPI cards (commits/day, productivity score, files per commit)
- Commit/day charts and heatmaps
- Module churn + LOC visuals
- Vibe panel (activates once commits are tagged)
- Recent commits table with AI indicators

Troubleshooting:
- Ensure the backend (Nov 7 build or later) is deployed—it adds the `/metrics` endpoint.
- Use a valid JWT token; metrics require authentication.

---

## Automation & API Reference

```
GET /metrics?days=30
Authorization: Bearer <JWT>
```

- `days` parameter accepts values 1–365 (default 30).
- Response includes `repository_summary`, `commits`, `lines_of_code`, `ai_effectiveness`, `recent_commits`.

### Example: weekly export

```bash
#!/bin/bash
TOKEN=$(gcloud auth print-identity-token)
curl -s "${API_BASE_URL}/metrics?days=90" \
  -H "Authorization: Bearer $TOKEN" \
  -o metrics-$(date +%Y-%m-%d).json
```

---

## Extending the Metrics

| Task | Location |
| ---- | -------- |
| Enhance collection logic | `web/backend/metrics.py` |
| Expose new fields | `web/backend/main.py` (`/metrics`) |
| Visualise in UI | `web/frontend/src/Metrics.jsx` |
| Styling tweaks | `web/frontend/src/Metrics.css` |
| Update docs/report | This page |

Recommended roadmap:
1. Tag vibe commits to enable AI vs manual charts.
2. Capture deployment metadata and test coverage in the metrics payload.
3. Add comparative charts (e.g., Provisioner vs Billing Agent) once data is available.

---

*Report regenerated: November 7, 2025.*

