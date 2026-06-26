from datetime import UTC, datetime
from typing import Any

from google.cloud import firestore

from app.config import settings


class AnalysisStore:
    def __init__(self) -> None:
        self._client = firestore.Client(
            project=settings.google_cloud_project,
            database=settings.firestore_database,
        )

    def create(self, analysis_id: str, payload: dict[str, Any]) -> None:
        self._client.collection("analyses").document(analysis_id).set(
            {
                **payload,
                "created_at": datetime.now(UTC),
                "updated_at": datetime.now(UTC),
            }
        )

    def update(self, analysis_id: str, payload: dict[str, Any]) -> None:
        self._client.collection("analyses").document(analysis_id).set(
            {
                **payload,
                "updated_at": datetime.now(UTC),
            },
            merge=True,
        )

    def get(self, analysis_id: str) -> dict[str, Any] | None:
        snapshot = self._client.collection("analyses").document(analysis_id).get()
        if not snapshot.exists:
            return None
        return snapshot.to_dict()
