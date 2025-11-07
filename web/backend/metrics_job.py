"""Entry point for Cloud Run Job that collects repository metrics snapshots."""

from __future__ import annotations

import argparse
import logging
import os
import subprocess
import tempfile
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List
from urllib.parse import quote

import metrics
from metrics_store import save_metrics_snapshot


DEFAULT_WINDOWS = [7, 30, 90, 180, 365]
DEFAULT_REPO_URL = "https://github.com/olivierizad-lab/gcp-billing-ai.git"
DEFAULT_BRANCH = "main"
ORIGINAL_REPO_ROOT = metrics.REPO_ROOT


@contextmanager
def cloned_repository(token: str, repo_url: str, branch: str):
    if not token:
        raise SystemExit("GITHUB_TOKEN environment variable is required")

    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir) / "repo"
        safe_token = quote(token, safe="")

        if repo_url.startswith("https://"):
            clone_url = repo_url.replace("https://", f"https://{safe_token}@", 1)
        else:
            clone_url = repo_url

        logging.info("Cloning repository %s (branch %s)", repo_url, branch)

        env = os.environ.copy()
        env.setdefault("GIT_TERMINAL_PROMPT", "0")

        try:
            subprocess.check_call(
                [
                    "git",
                    "clone",
                    "--branch",
                    branch,
                    clone_url,
                    str(repo_path),
                ],
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except subprocess.CalledProcessError as exc:
            logging.error("git clone failed: %s", exc)
            raise SystemExit("Failed to clone repository for metrics collection") from exc

        try:
            yield repo_path
        finally:
            # Ensure the cloned repo is removed (TemporaryDirectory handles cleanup)
            pass


def collect_metrics(windows: List[int]) -> Dict[str, Dict]:
    result: Dict[str, Dict] = {}

    for days in windows:
        try:
            logging.info("Collecting metrics for last %s days", days)
            window_metrics = metrics.get_all_metrics(days)
            commits = window_metrics.get("commits", [])
            repo_summary = window_metrics.get("repository_summary", {})
            print(
                f"[metrics_job] window={days} commits={len(commits)} total_commits={repo_summary.get('total_commits')} loc_summary={window_metrics.get('lines_of_code', {}).get('summary')}",
                flush=True,
            )
            window_metrics["analysis_period_days"] = days
            window_metrics.setdefault("generated_at", datetime.now(timezone.utc).isoformat())
            result[str(days)] = window_metrics
        except Exception as exc:
            logging.exception("Failed to collect metrics for %s-day window: %s", days, exc)

    return result


def main() -> None:
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(description="Collect repository metrics snapshots")
    parser.add_argument(
        "--windows",
        type=str,
        default=os.getenv("METRICS_WINDOWS", ",".join(str(w) for w in DEFAULT_WINDOWS)),
        help="Comma-separated list of analysis windows (in days)",
    )
    parser.add_argument(
        "--triggered-by",
        type=str,
        default=os.getenv("METRICS_TRIGGERED_BY", "job"),
        help="Optional label describing the trigger source (e.g. scheduler, manual)",
    )

    args = parser.parse_args()
    windows = [int(w.strip()) for w in args.windows.split(",") if w.strip()]
    if not windows:
        raise SystemExit("No analysis windows configured")

    token = os.getenv("GITHUB_TOKEN")
    repo_url = os.getenv("METRICS_REPO_URL", DEFAULT_REPO_URL)
    branch = os.getenv("METRICS_REPO_BRANCH", DEFAULT_BRANCH)

    logging.info("Starting metrics collection for windows: %s", windows)

    with cloned_repository(token, repo_url, branch) as repo_path:
        previous_repo_path = os.environ.get("METRICS_REPO_PATH")
        os.environ["METRICS_REPO_PATH"] = str(repo_path)
        metrics.REPO_ROOT = repo_path
        try:
            windows_metrics = collect_metrics(windows)
        finally:
            if previous_repo_path is not None:
                os.environ["METRICS_REPO_PATH"] = previous_repo_path
            else:
                os.environ.pop("METRICS_REPO_PATH", None)
            metrics.REPO_ROOT = ORIGINAL_REPO_ROOT

    if not windows_metrics:
        raise SystemExit("Metrics collection failed for all configured windows")

    snapshot_id = save_metrics_snapshot(
        windows_metrics,
        triggered_by=args.triggered_by,
        metadata={
            "windows": windows,
            "collected_at": datetime.now(timezone.utc).isoformat(),
            "repo_url": repo_url,
            "branch": branch,
        },
    )

    logging.info("Saved metrics snapshot %s covering %s windows", snapshot_id, windows)


if __name__ == "__main__":
    main()


