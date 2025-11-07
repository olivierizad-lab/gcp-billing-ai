# Development Metrics & Vibe Coding Analytics

The development metrics suite surfaces day-to-day engineering activity, long term velocity and the effectiveness of "vibe coding" (AI-assisted development). It mirrors the structure used in the Provisioner project and is built to answer three questions:

1. **How fast are we shipping?** (commit volume, lines of code, time-series trends)
2. **Where is the work happening?** (modules, services and languages affected)
3. **How much impact does vibe coding have?** (AI vs human authored work, assist frequency)

Metrics are collected by the backend (`/metrics` endpoint) and rendered in the web UI (`/metrics` route). All data can also be exported as JSON for scripting or reporting.

---

## Quick Reference

| Metric Family | What it captures | Sample visualisations |
| ------------- | ---------------- | ---------------------- |
| **Repository Summary** | Branch, latest tag, commit window, analysis timestamp | Header card stack |
| **Commit Activity** | Commits per day/week, author leaderboard, commit heatmap | Area chart + bar charts |
| **Module Footprint** | Lines of code, comment/test ratios per module & language | Stacked bar chart |
| **Vibe Coding** | AI authored commits, assisted LOC, time between assists | KPI cards + trend line |
| **Recent Activity** | Last 20 commits with AI attribution flags | Table |

> **Tip:** The analysis window defaults to 30 days. Adjust it with the `days` parameter (`GET /metrics?days=90`) or via the picker at the top of the UI.

---

## Vibe Coding Metrics

Vibe coding is detected using commit metadata. Commits are categorised as AI-assisted when the message contains one of the following markers:

- `Co-authored-by: vibe coding`
- `AI-Author: vibe`
- `#vibe`

### KPI Definitions

| KPI | Description |
| --- | ----------- |
| **AI Authored Commits** | Count and % of commits flagged with vibe markers. |
| **AI Assisted LOC** | Sum of `insertions + deletions` for AI commits. |
| **Assist Frequency** | Average hours between AI commits in the selected window. |
| **Top AI Contributors** | Authors ranked by % of their commits that were assisted. |

### Quick CLI Checks

```
# Show vibe commits in the last 30 days
git log --since="30 days ago" --format='%h %ad %an %s' | grep -i 'vibe'

# Compare AI vs non-AI commits per author
git log --since="30 days ago" --pretty='%an|%s' |
  awk -F'|' '{ if (tolower($2) ~ /vibe/) ai[$1]++; else manual[$1]++; }
             END { for (a in ai) printf "%s: AI=%d Manual=%d\n", a, ai[a], manual[a] }'
```

Encourage contributors to include one of the markers above whenever generative AI produces a meaningful chunk of code. The metrics dashboard relies on these flags for accuracy.

---

## Accessing the Dashboard

1. Sign in to the web UI.
2. Open the **Help** menu and click **Metrics**, or visit `/metrics` directly.
3. Choose the analysis window (7, 30, 90 days) and press **Refresh** to pull the latest data.

The dashboard is built with responsive cards:

- **Summary bar:** current branch/tag, total commits, AI usage ratio.
- **Activity charts:** daily commits (stacked AI vs manual) + cumulative LOC.
- **Heatmap:** hour/day matrix to visualise delivery cadence.
- **Module focus:** top services by churn with spark lines.
- **Vibe coding panel:** KPI tiles + trend line showing adoption over time.
- **Recent history:** data table with AI flag icons.

---

## API & Automation

```
GET /metrics?days=30
```

- `days` – optional, defaults to 30.
- Response payload contains `repository_summary`, `commit_statistics`, `lines_of_code`, `ai_effectiveness`, and `recent_commits`.

### Example request

```
curl -s "https://<BACKEND_URL>/metrics?days=30" | jq '.repository_summary, .ai_effectiveness'
```

### Scheduled exports

Add the following to a Cloud Scheduler job or cron task to capture a weekly snapshot:

```
#!/bin/bash
ts=$(date +%Y-%m-%d)
curl -s "https://<BACKEND_URL>/metrics?days=90" \
  -H "Authorization: Bearer $TOKEN" \
  -o metrics-$ts.json
```

---

## Extending the Metrics

| Task | Location |
| ---- | -------- |
| Calculate new statistics | `web/backend/metrics.py` |
| Expose them via the API | `web/backend/main.py` (`/metrics`) |
| Render in the UI | `web/frontend/src/Metrics.jsx` |
| Style updates | `web/frontend/src/Metrics.css` |
| Documentation update | This page |

When adding a new metric:

1. Add collection logic in `metrics.py` (store raw values + any pre-aggregated summaries).
2. Update the Pydantic schema (if introduced) so the API remains type-safe.
3. Extend the frontend components (cards, charts, table columns).
4. Document how to interpret the metric and any thresholds here.

---

## Troubleshooting

| Symptom | Resolution |
| ------- | ---------- |
| Dashboard shows "No data" | Ensure the backend has permission to fetch git history (Cloud Run service account needs `roles/source.reader`). |
| AI usage reads zero | Confirm commit messages include the vibe markers listed above. |
| API request fails with 401 | Include a valid `Authorization` bearer token (same as other authenticated endpoints). |
| Charts look empty after deployment | Run the backend with the latest commit; metrics rely on git history inside the container. |

---

## Related Files
- Backend collector: `web/backend/metrics.py`
- API handler: `web/backend/main.py` (`/metrics` route)
- Frontend dashboard: `web/frontend/src/Metrics.jsx`
- Stylesheet: `web/frontend/src/Metrics.css`

