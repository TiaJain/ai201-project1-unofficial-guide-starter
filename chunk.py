"""
chunk.py — Turn structured reviews into retrieval chunks.

Design decision (see planning.md):
RMP reviews are short (capped at ~350 chars) and each one is a single student's
complete, self-contained opinion. That makes one review the natural atomic unit
of retrieval. We therefore use a ONE-REVIEW-PER-CHUNK strategy rather than a
fixed character window:

  - Splitting a ~300-char review into smaller windows would fragment a single
    coherent thought ("his exams are" / "heavily curved") -> unretrievable halves.
  - Merging several reviews into one larger chunk would blend different students'
    opinions into one embedding, diluting the semantic signal so specific queries
    can't match precisely.

Each chunk carries metadata: source file, course, quality, difficulty, and a
chunk_id encoding the source and the review's position in that source. The
course + professor name are prepended to the chunk TEXT as a short context line
so a chunk is meaningful on its own even if a review never names the professor
(addresses the "missing name" risk in planning.md).

Safety net: if any single review were ever longer than MAX_CHARS (RMP caps make
this rare), we fall back to splitting it into overlapping windows so no chunk is
oversized.
"""

import json
import re

REVIEWS_IN = "reviews.json"
CHUNKS_OUT = "chunks.json"

MAX_CHARS = 600        # only triggers the fallback splitter for unusually long text
OVERLAP = 50           # overlap used only by the fallback splitter


def professor_name_from_source(source):
    """data/hilfinger.txt -> 'Hilfinger'. Used to prepend context to chunks."""
    base = re.sub(r"\.txt$", "", source)
    return base.capitalize()


def split_long(text, max_chars=MAX_CHARS, overlap=OVERLAP):
    """Fallback: window-split text that exceeds max_chars, on word boundaries."""
    if len(text) <= max_chars:
        return [text]
    words = text.split()
    chunks, cur = [], ""
    for w in words:
        if len(cur) + len(w) + 1 > max_chars and cur:
            chunks.append(cur.strip())
            # start next window with overlap tail of the previous one
            tail = cur[-overlap:]
            cur = tail + " " + w
        else:
            cur = (cur + " " + w).strip()
    if cur:
        chunks.append(cur.strip())
    return chunks


def build_chunks(reviews):
    chunks = []
    per_source_counter = {}

    for r in reviews:
        source = r["source"]
        idx = per_source_counter.get(source, 0)
        per_source_counter[source] = idx + 1

        prof = professor_name_from_source(source)
        course = r["course"] or "unknown course"
        # Prepend a short context line so the chunk stands alone.
        context = f"Review of Professor {prof} ({course}): "

        pieces = split_long(r["text"])
        for sub_i, piece in enumerate(pieces):
            chunk_id = f"{source}::review_{idx}"
            if len(pieces) > 1:
                chunk_id += f"::part_{sub_i}"
            chunks.append({
                "chunk_id": chunk_id,
                "text": context + piece,
                "metadata": {
                    "source": source,
                    "professor": prof,
                    "course": course,
                    "quality": r["quality"],
                    "difficulty": r["difficulty"],
                    "review_index": idx,
                },
            })
    return chunks


def main():
    reviews = json.load(open(REVIEWS_IN, encoding="utf-8"))
    chunks = build_chunks(reviews)

    json.dump(chunks, open(CHUNKS_OUT, "w", encoding="utf-8"), indent=2)

    lens = sorted(len(c["text"]) for c in chunks)
    print(f"Built {len(chunks)} chunks from {len(reviews)} reviews")
    print(f"Chunk char length: min={lens[0]} median={lens[len(lens)//2]} max={lens[-1]}")
    print(f"Wrote {CHUNKS_OUT}\n")

    # --- Inspection: print 5 representative chunks (milestone requirement) ---
    import random
    random.seed(7)
    sample = random.sample(chunks, min(5, len(chunks)))
    print("=" * 70)
    print("5 RANDOM CHUNKS — each should be readable, substantive, self-contained")
    print("=" * 70)
    for c in sample:
        print(f"\n[{c['chunk_id']}]")
        print(c["text"])


if __name__ == "__main__":
    main()
