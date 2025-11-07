"""Utility helpers for storing and retrieving metrics snapshots in Firestore."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from google.cloud import firestore


PROJECT_ID = (
    os.getenv("BQ_PROJECT")
    or os.getenv("GCP_PROJECT_ID")
    or os.getenv("GOOGLE_CLOUD_PROJECT")
    or "qwiklabs-asl-04-8e9f23e85ced"
)

COLLECTION_NAME = os.getenv("METRICS_COLLECTION", "metrics_snapshots")

_db: Optional[firestore.Client] = None


def _get_db() -> firestore.Client:
    global _db
    if _db is None:
        _db = firestore.Client(project=PROJECT_ID)
    return _db


def save_metrics_snapshot(
    windows: Dict[str, Dict[str, Any]],
    *,
    triggered_by: str = "job",
    metadata: Optional[Dict[str, Any]] = None,
) -> str:
    """Persist a metrics snapshot covering one or more analysis windows."""

    if not windows:
        raise ValueError("windows is empty; nothing to persist")

    db = _get_db()
    doc_ref = db.collection(COLLECTION_NAME).document()

    snapshot_time = datetime.now(timezone.utc)

    payload: Dict[str, Any] = {
        "windows": windows,
        "triggered_by": triggered_by,
        "metadata": metadata or {},
        "available_days": sorted(int(day) for day in windows.keys()),
        "created_at": firestore.SERVER_TIMESTAMP,
        "created_at_iso": snapshot_time.isoformat(),
    }

    doc_ref.set(payload)
    return doc_ref.id


def get_latest_snapshot(days: Optional[int] = None) -> Optional[Dict[str, Any]]:
    """Fetch the latest metrics snapshot, optionally filtered by analysis window."""

    db = _get_db()
    query = (
        db.collection(COLLECTION_NAME)
        .order_by("created_at", direction=firestore.Query.DESCENDING)
        .limit(5)
    )

    for doc in query.stream():
        data = doc.to_dict() or {}
        windows: Dict[str, Dict[str, Any]] = data.get("windows", {})

        key = str(days) if days is not None else None

        if key is None:
            # use the first available window in this snapshot
            if not windows:
                continue
            first_key, metrics = _select_first_window(windows)
            return _build_snapshot_response(doc.id, data, first_key, metrics)

        if key in windows:
            metrics = windows[key]
            return _build_snapshot_response(doc.id, data, key, metrics)

    return None


def _select_first_window(windows: Dict[str, Dict[str, Any]]) -> Tuple[str, Dict[str, Any]]:
    # Prefer the smallest analysis window for deterministic behaviour
    sorted_items = sorted(((int(k), k) for k in windows.keys()))
    _, selected_key = sorted_items[0]
    return selected_key, windows[selected_key]


def _build_snapshot_response(
    doc_id: str,
    data: Dict[str, Any],
    key: str,
    metrics: Dict[str, Any],
) -> Dict[str, Any]:
    # Ensure metadata is present on the metrics payload for convenience
    metrics = dict(metrics)
    metrics.setdefault("analysis_period_days", int(key))

    created_iso = data.get("created_at_iso")
    available_days = data.get("available_days") or [int(k) for k in data.get("windows", {}).keys()]

    return {
        "id": doc_id,
        "metrics": metrics,
        "generated_at": created_iso,
        "available_days": sorted(int(day) for day in available_days),
        "triggered_by": data.get("triggered_by", "job"),
        "metadata": data.get("metadata", {}),
    }


def clear_snapshots(limit: int = 100) -> int:
    """Utility for pruning old snapshots. Returns number of documents deleted."""

    db = _get_db()
    query = (
        db.collection(COLLECTION_NAME)
        .order_by("created_at", direction=firestore.Query.DESCENDING)
        .offset(limit)
    )

    deleted = 0
    for doc in query.stream():
        doc.reference.delete()
        deleted += 1
    return deleted


