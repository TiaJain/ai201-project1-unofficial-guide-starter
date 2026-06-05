"""
embed.py — Embed chunks with all-MiniLM-L6-v2 and store them in ChromaDB.

Pipeline position:  ... -> Chunking (chunks.json) -> [Embedding + Vector Store] -> Retrieval -> Generation

- Loads chunks.json (produced by chunk.py).
- Embeds each chunk's text locally with sentence-transformers all-MiniLM-L6-v2
  (no API key, no rate limits, 384-dim vectors).
- Stores vectors in a persistent ChromaDB collection along with metadata
  (source file, professor, course, quality, difficulty, review index) so we can
  attribute answers to their source document later.

Run once to build the index:  python3 embed.py
The DB persists in ./chroma_db so you don't re-embed every run.
"""

import json
import chromadb
from sentence_transformers import SentenceTransformer

CHUNKS_IN = "chunks.json"
DB_DIR = "chroma_db"
COLLECTION_NAME = "rmp_reviews"
MODEL_NAME = "all-MiniLM-L6-v2"


def main():
    chunks = json.load(open(CHUNKS_IN, encoding="utf-8"))
    print(f"Loaded {len(chunks)} chunks from {CHUNKS_IN}")

    # Load the local embedding model (downloads ~90MB on first run, then cached).
    print(f"Loading embedding model: {MODEL_NAME} ...")
    model = SentenceTransformer(MODEL_NAME)

    # Persistent client so the index survives between runs.
    client = chromadb.PersistentClient(path=DB_DIR)

    # Start fresh each build so re-runs don't duplicate or stale-mix entries.
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    # cosine space -> distances in [0, 2]; closer to 0 = more similar.
    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    texts = [c["text"] for c in chunks]
    ids = [c["chunk_id"] for c in chunks]
    metadatas = [
        {
            "source": c["metadata"]["source"],
            "professor": c["metadata"]["professor"],
            "course": c["metadata"]["course"],
            "quality": c["metadata"]["quality"],
            # ChromaDB metadata values can't be None; coerce missing difficulty.
            "difficulty": c["metadata"]["difficulty"]
            if c["metadata"]["difficulty"] is not None else -1.0,
            "review_index": c["metadata"]["review_index"],
        }
        for c in chunks
    ]

    print("Embedding chunks (this is the slow step) ...")
    embeddings = model.encode(
        texts, batch_size=64, show_progress_bar=True, convert_to_numpy=True
    ).tolist()

    # Add in batches to stay well under ChromaDB's per-call limits.
    B = 500
    for i in range(0, len(ids), B):
        collection.add(
            ids=ids[i:i + B],
            documents=texts[i:i + B],
            embeddings=embeddings[i:i + B],
            metadatas=metadatas[i:i + B],
        )

    print(f"\nStored {collection.count()} chunks in ChromaDB collection "
          f"'{COLLECTION_NAME}' at ./{DB_DIR}")


if __name__ == "__main__":
    main()
