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

"""Chunks Customer Experience policies and indexes them into Cloud Firestore with Agent Platform vector embeddings.

Usage:
    python3 customer_agent/scripts/index_knowledge_base.py
"""

import os
import re
from dotenv import load_dotenv

load_dotenv()

PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT", "has-demo-500917")
LOCATION = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
KB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data",
    "customer_experience_knowledge_base.md",
)


def chunk_markdown(text: str) -> list[dict]:
    sections = re.split(r"(?m)^## ", text)
    chunks = []
    for section in sections[1:]:
        title, _, body = section.partition("\n")
        clean_title = title.strip()
        slug = re.sub(r"[^a-zA-Z0-9]+", "-", clean_title.lower()).strip("-")
        chunks.append({
            "slug": slug,
            "title": clean_title,
            "content": f"## {clean_title}\n{body.strip()}",
        })
    return chunks


def main():
    print(f"Reading knowledge base from {KB_PATH}...")
    with open(KB_PATH, encoding="utf-8") as f:
        content = f.read()

    chunks = chunk_markdown(content)
    print(f"Extracted {len(chunks)} policy chunks.")

    print(f"Connecting to Cloud Firestore & Agent Platform in project '{PROJECT_ID}'...")
    try:
        from google.cloud import firestore
        from google.cloud.firestore_v1.vector import Vector
        import vertexai
        from vertexai.language_models import TextEmbeddingModel

        vertexai.init(project=PROJECT_ID, location=LOCATION)
        embedding_model = TextEmbeddingModel.from_pretrained("text-embedding-004")
        db = firestore.Client(project=PROJECT_ID)

        print("Generating embeddings and writing to Firestore 'policies' collection...")
        for chunk in chunks:
            embeddings = embedding_model.get_embeddings([chunk["content"]])
            vector_data = Vector(embeddings[0].values)
            doc_data = {
                "slug": chunk["slug"],
                "title": chunk["title"],
                "content": chunk["content"],
                "embedding": vector_data,
            }
            db.collection("policies").document(chunk["slug"]).set(doc_data)
            print(f"  - Indexed '{chunk['title']}' (slug: {chunk['slug']}) with 768-dim vector")

        print("Knowledge base indexing into Cloud Firestore complete.")

    except Exception as e:
        print(f"Cloud Firestore / Agent Platform indexing encountered an error: {e}")
        print("Note: In local mock / test environments, in-memory fallback handles retrieval automatically.")


if __name__ == "__main__":
    main()
