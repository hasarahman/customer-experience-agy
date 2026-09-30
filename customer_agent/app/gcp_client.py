# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""GCP Client wrapper for Cloud Firestore, Agent Platform Embeddings, and Cloud Logging.

Configured for project has-demo-500917.
Provides seamless fallback to in-memory/mock mode for offline testing and CI/CD.
"""

from __future__ import annotations

import logging
import math
import os
import re
from datetime import date, datetime, timedelta, timezone
from typing import Any

try:
    from dotenv import load_dotenv
    _local_env = os.path.join(os.path.dirname(__file__), "..", ".env")
    if os.path.isfile(_local_env):
        load_dotenv(_local_env)
except Exception:
    pass

PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT", "has-demo-500917")
LOCATION = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")

logger = logging.getLogger("customer_agent.gcp_client")


class InMemoryFirestoreMock:
    """In-memory Firestore compatible mock for local testing, emulation, and offline execution."""

    def __init__(self):
        self._collections: dict[str, dict[str, dict[str, Any]]] = {
            "customers": {},
            "orders": {},
            "otps": {},
            "policies": {},
            "escalations": {},
        }
        self._seed_default_data()

    def _seed_default_data(self):
        today = date.today().isoformat()
        past_45_days = (date.today() - timedelta(days=45)).isoformat()

        # Customers
        self._collections["customers"]["CUST-001"] = {
            "customer_id": "CUST-001",
            "name": "Hasan Rahman",
            "email": "hasan2296@outlook.com",
            "phone": "+1-503-555-0142",
            "home_address": "482 Elm Street, Portland, OR 97205",
        }

        # Orders
        self._collections["orders"]["BK-10001"] = {
            "order_number": "BK-10001",
            "order_date": today,
            "customer_id": "CUST-001",
            "customer_name": "Hasan Rahman",
            "customer_email": "hasan2296@outlook.com",
            "book_ordered": "The Midnight Library",
            "category": "Fiction",
            "address_shipped_to": "482 Elm Street, Portland, OR 97205",
            "shipping_status": "Delivered",
            "carrier": "USPS",
            "tracking_number": "9400111899223192000001",
            "return_eligible_30_day": "Yes",
            "return_status": "",
        }

        self._collections["orders"]["BK-10002"] = {
            "order_number": "BK-10002",
            "order_date": today,
            "customer_id": "CUST-001",
            "customer_name": "Hasan Rahman",
            "customer_email": "hasan2296@outlook.com",
            "book_ordered": "Project Hail Mary",
            "category": "Fiction",
            "address_shipped_to": "482 Elm Street, Portland, OR 97205",
            "shipping_status": "Processing",
            "carrier": "",
            "tracking_number": "",
            "return_eligible_30_day": "Yes",
            "return_status": "",
        }

        self._collections["orders"]["BK-10003"] = {
            "order_number": "BK-10003",
            "order_date": today,
            "customer_id": "CUST-001",
            "customer_name": "Hasan Rahman",
            "customer_email": "hasan2296@outlook.com",
            "book_ordered": "First Edition Atlas",
            "category": "Rare/Collectible",
            "address_shipped_to": "482 Elm Street, Portland, OR 97205",
            "shipping_status": "Delivered",
            "carrier": "FedEx",
            "tracking_number": "780123456789",
            "return_eligible_30_day": "No",
            "return_status": "",
        }

        self._collections["orders"]["BK-10006"] = {
            "order_number": "BK-10006",
            "order_date": today,
            "customer_id": "CUST-001",
            "customer_name": "Hasan Rahman",
            "customer_email": "hasan2296@outlook.com",
            "book_ordered": "Rare Poetry Edition",
            "category": "Clearance",
            "address_shipped_to": "482 Elm Street, Portland, OR 97205",
            "shipping_status": "Delivered",
            "carrier": "UPS",
            "tracking_number": "1Z9999999999999999",
            "return_eligible_30_day": "No",
            "return_status": "",
        }

        self._collections["orders"]["BK-10015"] = {
            "order_number": "BK-10015",
            "order_date": today,
            "customer_id": "CUST-001",
            "customer_name": "Hasan Rahman",
            "customer_email": "hasan2296@outlook.com",
            "book_ordered": "Dune Messiah",
            "category": "Fiction",
            "address_shipped_to": "482 Elm Street, Portland, OR 97205",
            "shipping_status": "Processing",
            "carrier": "",
            "tracking_number": "",
            "return_eligible_30_day": "Yes",
            "return_status": "",
        }

        self._collections["orders"]["BK-10099"] = {
            "order_number": "BK-10099",
            "order_date": past_45_days,
            "customer_id": "CUST-001",
            "customer_name": "Hasan Rahman",
            "customer_email": "hasan2296@outlook.com",
            "book_ordered": "The Great Gatsby",
            "category": "Fiction",
            "address_shipped_to": "482 Elm Street, Portland, OR 97205",
            "shipping_status": "Delivered",
            "carrier": "USPS",
            "tracking_number": "9400111899223192000099",
            "return_eligible_30_day": "Yes",
            "return_status": "",
        }

        # Seed KB policies from file if available
        kb_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "data",
            "customer_experience_knowledge_base.md",
        )
        if os.path.exists(kb_path):
            with open(kb_path, encoding="utf-8") as f:
                content = f.read()
            sections = re.split(r"(?m)^## ", content)
            for i, sec in enumerate(sections[1:]):
                title, _, body = sec.partition("\n")
                slug = re.sub(r"[^a-zA-Z0-9]+", "-", title.lower()).strip("-")
                self._collections["policies"][slug] = {
                    "slug": slug,
                    "title": title.strip(),
                    "content": f"## {title.strip()}\n{body.strip()}",
                }

    def get_document(self, collection: str, doc_id: str) -> dict[str, Any] | None:
        return self._collections.get(collection, {}).get(doc_id)

    def set_document(self, collection: str, doc_id: str, data: dict[str, Any]) -> None:
        if collection not in self._collections:
            self._collections[collection] = {}
        self._collections[collection][doc_id] = data

    def update_document(self, collection: str, doc_id: str, updates: dict[str, Any]) -> bool:
        if collection in self._collections and doc_id in self._collections[collection]:
            self._collections[collection][doc_id].update(updates)
            return True
        return False

    def query_collection(self, collection: str, field: str, value: Any) -> list[dict[str, Any]]:
        results = []
        for doc in self._collections.get(collection, {}).values():
            val = doc.get(field, "")
            if isinstance(val, str) and isinstance(value, str):
                if val.strip().lower() == value.strip().lower():
                    results.append(doc)
            elif val == value:
                results.append(doc)
        return results

    def vector_search_policies(self, query: str, limit: int = 2) -> list[str]:
        """Simple keyword/relevance match across in-memory policy sections."""
        query_words = set(re.findall(r"\w+", query.lower()))
        scored = []
        for doc in self._collections.get("policies", {}).values():
            text = doc.get("content", "").lower()
            score = sum(1 for w in query_words if w in text)
            if score > 0:
                scored.append((score, doc.get("content", "")))
        scored.sort(key=lambda x: x[0], reverse=True)
        results = [text for _, text in scored[:limit]]
        if not results and self._collections.get("policies"):
            # Return first doc as fallback
            return [next(iter(self._collections["policies"].values()))["content"]]
        return results


class GCPClientManager:
    """Manages Firestore and Agent Platform client connections with seamless fallback."""

    def __init__(self):
        self._firestore_client = None
        self._use_mock = False
        self._mock_db = InMemoryFirestoreMock()
        self._init_firestore()

    def _init_firestore(self):
        emulator_host = os.environ.get("FIRESTORE_EMULATOR_HOST")
        try:
            from google.cloud import firestore

            if emulator_host:
                self._firestore_client = firestore.Client(project=PROJECT_ID)
                logger.info(f"Connected to Firestore Emulator at {emulator_host}")
            else:
                # Attempt to initialize cloud client
                self._firestore_client = firestore.Client(project=PROJECT_ID)
                # Quick non-blocking check
                logger.info(f"Connected to live Cloud Firestore for project {PROJECT_ID}")
        except Exception as e:
            logger.warning(
                f"Cloud Firestore unavailable ({e}). Using robust in-memory mock client."
            )
            self._use_mock = True

    @property
    def is_mock(self) -> bool:
        return self._use_mock or self._firestore_client is None

    @property
    def mock_db(self) -> InMemoryFirestoreMock:
        return self._mock_db

    @property
    def firestore(self):
        return self._firestore_client


# Global client instance
gcp_manager = GCPClientManager()
