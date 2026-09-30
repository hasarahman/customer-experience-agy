"""Generic Knowledge Base Chunking & Vector Indexer.

Reads markdown policy documents, splits them into semantic chunks, generates
Agent Platform text-embedding-004 vector embeddings, and stores them in Firestore.
"""

import os
import sys
from typing import List, Dict

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app.gcp_client import gcp_manager


def chunk_markdown(file_path: str) -> List[Dict[str, str]]:
    """Split markdown file into sections based on '## ' headers."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Knowledge base file not found: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    chunks = []
    sections = content.split("\n## ")

    # Handle intro section before first ##
    if sections and not sections[0].startswith("## "):
        intro = sections[0].strip()
        if intro:
            chunks.append({"section": "Overview", "content": intro})
        sections = sections[1:]

    for sec in sections:
        lines = sec.strip().split("\n", 1)
        title = lines[0].strip("# ").strip()
        body = lines[1].strip() if len(lines) > 1 else ""
        if title:
            chunks.append({
                "section": title,
                "content": f"## {title}\n{body}"
            })

    return chunks


def index_knowledge_base(kb_file: str, collection_name: str = "policies"):
    """Index chunks with embeddings into Firestore."""
    db = gcp_manager.firestore
    chunks = chunk_markdown(kb_file)
    print(f"Found {len(chunks)} sections in {kb_file}.")

    for idx, chunk in enumerate(chunks):
        doc_id = f"policy_{idx:03d}_{chunk['section'].lower().replace(' ', '_')}"
        text_to_embed = f"{chunk['section']}: {chunk['content']}"

        embedding = gcp_manager.get_embedding(text_to_embed)
        if embedding:
            print(f"[{idx+1}/{len(chunks)}] Embedded '{chunk['section']}' (dim: {len(embedding)})")
        else:
            print(f"[{idx+1}/{len(chunks)}] Mock mode (no embedding) for '{chunk['section']}'")

        doc_data = {
            "section": chunk["section"],
            "content": chunk["content"],
            "embedding": embedding,
        }
        db.collection(collection_name).document(doc_id).set(doc_data)

    print(f"\nSuccessfully indexed {len(chunks)} policy chunks into '{collection_name}' collection.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python index_kb.py <path_to_markdown_file>")
        sys.exit(1)
    index_knowledge_base(sys.argv[1])
