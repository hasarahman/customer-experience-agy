# Agent Platform Embeddings & RAG Vector Search in Firestore

This reference documents the implementation of vector search and knowledge base grounding using Agent Platform `text-embedding-004` and Cloud Firestore.

---

## 1. Embeddings Model Specification

- **Model**: `text-embedding-004`
- **Output Dimensionality**: 768 dimensions (float list)
- **SDK**: `google-genai` client:
  ```python
  from google import genai
  client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)
  response = client.models.embed_content(
      model="text-embedding-004",
      contents=text_query
  )
  embedding = response.embeddings[0].values  # List of 768 floats
  ```

---

## 2. Markdown Chunking Strategy

Avoid arbitrary character splitting, which truncates policy sentences or separates rules from their headers. Split along semantic markdown headings (`## `):

```python
def chunk_markdown(content: str) -> list[dict]:
    chunks = []
    sections = content.split("\n## ")
    for sec in sections:
        if not sec.strip():
            continue
        lines = sec.strip().split("\n", 1)
        title = lines[0].strip("# ").strip()
        body = lines[1].strip() if len(lines) > 1 else ""
        chunks.append({
            "section": title,
            "content": f"## {title}\n{body}"
        })
    return chunks
```

---

## 3. Cosine Similarity Vector Retrieval

When searching policies for grounding without needing full Firestore Vector Search extensions:

```python
import math

def cosine_similarity(v1: list[float], v2: list[float]) -> float:
    dot = sum(a * b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot / (norm1 * norm2)

def search_policy_kb(query: str, top_k: int = 2) -> dict:
    query_emb = gcp_manager.get_embedding(query)
    policies_ref = gcp_manager.firestore.collection("policies")
    
    scored_chunks = []
    for doc in policies_ref.stream():
        data = doc.to_dict()
        doc_emb = data.get("embedding")
        if doc_emb and query_emb:
            sim = cosine_similarity(query_emb, doc_emb)
            scored_chunks.append((sim, data))
            
    scored_chunks.sort(key=lambda x: x[0], reverse=True)
    results = [
        {"section": d["section"], "content": d["content"], "similarity": round(s, 4)}
        for s, d in scored_chunks[:top_k]
    ]
    return {"results": results}
```

---

## 4. Agent Tool Instruction

Instruct the agent to prioritize policy lookups and never hallucinate numbers:

```markdown
## Policy Grounding
ALWAYS call search_policy_kb for any question about shipping times/costs, returns, payment,
passwords, or company policy — even if it doesn't contain the word "policy," and even if you feel
confident you already know the answer. Never answer these from your own general knowledge or
typical industry norms.
```
