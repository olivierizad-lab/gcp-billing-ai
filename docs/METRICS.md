# Code Metrics & AI Effectiveness Dashboard

## Overview
The metrics dashboard provides visibility into repository productivity, code quality and AI-assisted development effectiveness. Metrics are collected by the backend (`/metrics` endpoint) and visualised in the frontend metrics page.

## Accessing the Dashboard

1. Open the web UI and sign in.
2. Click the `Help` button and select **Metrics** (or navigate directly to `/metrics`).
3. Use the filters at the top of the page to choose the analysis window (default is 30 days) and refresh the data when needed.

## Metrics Captured

### AI Effectiveness
- **AI authored commits** – number, percentage and lines of code attributed to AI generated commits (messages that contain "Co-authored-by: vibe coding").
- **Assisted vs manual breakdown** – compares AI-assisted work with traditional commits by author and by files touched.
- **Time between assists** – average hours between AI-assisted commits to identify usage trends.

### Commit Statistics
- Top contributors by commits and lines of code.
- Commit volume heatmap showing activity across days of week and hours of day.
- Rolling commit velocity (daily, weekly and monthly trends).

### Lines of Code by Module
- Per-module totals for lines of code, comments, tests and files.
- Breakdown by language with growth over the selected analysis window.

### Repository Summary
- Current git branch and tag information.
- Metrics generation timestamp and analysis window.

## API Endpoint
Metrics are retrieved from the backend endpoint:

```
GET /metrics?days=30
```

- `days` parameter controls the analysis window (default 30).
- Response contains `repository_summary`, `commit_statistics`, `lines_of_code`, `ai_effectiveness`, and a detailed list of recent commits.

## Adding New Metrics
1. Update `web/backend/metrics.py` to collect additional data points.
2. Extend the `/metrics` response schema with the new fields.
3. Update `web/frontend/src/Metrics.jsx` to render new visualisations.
4. Add documentation to this page summarising the new metrics.

## Related Files
- Backend: `web/backend/metrics.py`
- Frontend page: `web/frontend/src/Metrics.jsx`
- Styles: `web/frontend/src/Metrics.css`
- API endpoint: `web/backend/main.py` (`/metrics` route)

