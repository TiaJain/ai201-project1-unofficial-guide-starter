"""
retrieve.py — Semantic retrieval over the ChromaDB index.

Provides retrieve(query, k=5) -> list of dicts with text, source metadata, and
distance score. Lower distance = more similar (cosine distance, range ~0-2).

Run directly to test retrieval against the evaluation-plan questions:
    python3 retrieve.py
"""

import chromadb
from sentence_transformers import SentenceTransformer

DB_DIR = "chroma_db"
COLLECTION_NAME = "rmp_reviews"
MODEL_NAME = "all-MiniLM-L6-v2"

# Load model + collection once at import (reused across queries).
_model = SentenceTransformer(MODEL_NAME)
_client = chromadb.PersistentClient(path=DB_DIR)
_collection = _client.get_collection(COLLECTION_NAME)


def retrieve(query, k=5):
    """Return the top-k most similar chunks to `query`."""
    q_emb = _model.encode([query], convert_to_numpy=True).tolist()
    res = _collection.query(query_embeddings=q_emb, n_results=k)

    results = []
    for doc, meta, dist in zip(
        res["documents"][0], res["metadatas"][0], res["distances"][0]
    ):
        results.append({
            "text": doc,
            "source": meta["source"],
            "professor": meta["professor"],
            "course": meta["course"],
            "quality": meta["quality"],
            "difficulty": meta["difficulty"],
            "distance": dist,
        })
    return results


# The 5 evaluation-plan questions (from planning.md).
EVAL_QUESTIONS = [
    "What do students say about Paul Hilfinger's lectures and projects in CS 61B?",
    "How do students describe John DeNero as a CS 61A instructor?",
    "What's the student consensus on Satish Rao's teaching style and exams in CS 170?",
    "Do students find Babak Ayazifar's exams difficult, and would they recommend him?",
    "What do students say about Josh Hug's CS 61B lectures versus his exams and workload?",
]


def _test():
    for q in EVAL_QUESTIONS:
        print("=" * 78)
        print("QUERY:", q)
        print("=" * 78)
        for i, r in enumerate(retrieve(q, k=5), 1):
            print(f"\n  #{i}  distance={r['distance']:.3f}  "
                  f"[{r['source']} | {r['course']} | Q={r['quality']} D={r['difficulty']}]")
            print(f"      {r['text']}")
        print()


if __name__ == "__main__":
    _test()