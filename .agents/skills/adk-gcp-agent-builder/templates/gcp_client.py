"""GCP Client Singleton & Adapter for ADK Agents.

Provides access to Cloud Firestore and Agent Platform Embeddings with seamless
fallback to an in-memory dictionary store when running without GCP credentials.
"""

import math
import os
from typing import Any, Dict, List, Optional


def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """Compute cosine similarity between two numeric vectors."""
    dot = sum(a * b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot / (norm1 * norm2)


class MockDocumentSnapshot:
    """In-memory mock of a Firestore DocumentSnapshot."""

    def __init__(self, doc_id: str, data: Optional[Dict[str, Any]]):
        self.id = doc_id
        self._data = data

    @property
    def exists(self) -> bool:
        return self._data is not None

    def to_dict(self) -> Optional[Dict[str, Any]]:
        return dict(self._data) if self._data else None


class MockDocumentReference:
    """In-memory mock of a Firestore DocumentReference."""

    def __init__(self, store: Dict[str, Dict[str, Any]], collection_name: str, doc_id: str):
        self._store = store
        self._col = collection_name
        self.id = doc_id

    def get(self) -> MockDocumentSnapshot:
        col_data = self._store.get(self._col, {})
        data = col_data.get(self.id)
        return MockDocumentSnapshot(self.id, data)

    def set(self, data: Dict[str, Any], merge: bool = False) -> None:
        if self._col not in self._store:
            self._store[self._col] = {}
        if merge and self.id in self._store[self._col]:
            self._store[self._col][self.id].update(data)
        else:
            self._store[self._col][self.id] = dict(data)

    def update(self, data: Dict[str, Any]) -> None:
        if self._col not in self._store or self.id not in self._store[self._col]:
            raise KeyError(f"Document {self.id} does not exist in {self._col}")
        self._store[self._col][self.id].update(data)


class MockCollectionReference:
    """In-memory mock of a Firestore CollectionReference."""

    def __init__(self, store: Dict[str, Dict[str, Any]], collection_name: str):
        self._store = store
        self._col = collection_name

    def document(self, doc_id: str) -> MockDocumentReference:
        return MockDocumentReference(self._store, self._col, doc_id)

    def stream(self):
        col_data = self._store.get(self._col, {})
        for doc_id, data in col_data.items():
            yield MockDocumentSnapshot(doc_id, data)


class MockFirestoreClient:
    """In-memory mock of google.cloud.firestore.Client."""

    def __init__(self):
        self._store: Dict[str, Dict[str, Any]] = {}

    def collection(self, collection_name: str) -> MockCollectionReference:
        return MockCollectionReference(self._store, collection_name)


class GCPManager:
    """Central singleton managing Cloud Firestore and Agent Platform clients."""

    def __init__(self):
        self.project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
        self._firestore = None
        self._genai_client = None

    @property
    def is_live_gcp(self) -> bool:
        return bool(self.project_id)

    @property
    def firestore(self):
        if self._firestore is None:
            if self.project_id:
                try:
                    from google.cloud import firestore
                    self._firestore = firestore.Client(project=self.project_id)
                except Exception as e:
                    print(f"Warning: Failed to initialize live Firestore ({e}), falling back to mock.")
                    self._firestore = MockFirestoreClient()
            else:
                self._firestore = MockFirestoreClient()
        return self._firestore

    @property
    def genai_client(self):
        if self._genai_client is None and self.project_id:
            try:
                from google import genai
                self._genai_client = genai.Client(
                    vertexai=True,
                    project=self.project_id,
                    location=os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
                )
            except Exception as e:
                print(f"Warning: Failed to initialize Agent Platform client ({e}).")
        return self._genai_client

    def get_embedding(self, text: str, model: str = "text-embedding-004") -> Optional[List[float]]:
        """Fetch 768-dimensional text embeddings from Agent Platform."""
        if not self.genai_client:
            return None
        try:
            resp = self.genai_client.models.embed_content(
                model=model,
                contents=text
            )
            return resp.embeddings[0].values
        except Exception as e:
            print(f"Embedding error: {e}")
            return None


gcp_manager = GCPManager()
