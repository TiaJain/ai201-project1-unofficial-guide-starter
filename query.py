"""
query.py — End-to-end grounded question answering.

Pipeline: question -> retrieve top-k chunks (ChromaDB) -> build grounded prompt
-> Groq llama-3.3-70b-versatile -> {answer, sources}.

Grounding is enforced two ways:
  1. The system prompt instructs the model to answer ONLY from the provided
     context and to refuse ("I don't have enough information on that.") when the
     context is insufficient.
  2. Source attribution is computed in code from the retrieved chunks' metadata,
     so attribution is guaranteed correct regardless of what the model writes.

Requires:
  - GROQ_API_KEY in a .env file (or the environment)
  - A populated ChromaDB collection (run embed.py first)
"""

import os
from collections import OrderedDict

from dotenv import load_dotenv
from groq import Groq

from retrieve import retrieve

load_dotenv()

MODEL = "llama-3.3-70b-versatile"
TOP_K = 5

# A weak top result means the corpus probably doesn't cover the question.
# Cosine distances on real eval questions ran 0.16-0.31; anything past this is
# a different topic. Used as a pre-LLM gate so we refuse before generating.
DISTANCE_CUTOFF = 0.55

SYSTEM_PROMPT = """You are a question-answering assistant for an unofficial guide \
to UC Berkeley CS professors, built from student reviews on Rate My Professors.

Rules you must follow exactly:
1. Answer ONLY using the information in the CONTEXT provided in the user message. \
The context is a set of real student reviews. Treat it as your only source of truth.
2. Do NOT use any outside or prior knowledge about these professors, courses, or \
UC Berkeley. If you happen to know something that is not in the context, you must \
not use it.
3. If the context does not contain enough information to answer the question, \
respond with exactly: "I don't have enough information on that." Do not guess, \
do not hedge, do not pad with general advice.
4. When the context contains conflicting opinions, reflect the disagreement \
honestly (e.g. "reviews are split: some say X, others say Y") rather than picking \
one side.
5. Be concise and specific. Attribute claims to what students/reviews say, not to \
established fact.

You will be given the CONTEXT and then a QUESTION."""

USER_TEMPLATE = """CONTEXT:
{context}

QUESTION: {question}

Answer using only the context above. If the context is insufficient, say exactly \
"I don't have enough information on that." """


def _format_context(chunks):
    """Render retrieved chunks into a numbered context block for the prompt."""
    lines = []
    for i, c in enumerate(chunks, 1):
        prof = c.get("professor", "Unknown")
        course = c.get("course", "")
        src = c.get("source", "unknown")
        header = f"[{i}] (professor: {prof}, course: {course}, source: {src})"
        lines.append(f"{header}\n{c['text']}")
    return "\n\n".join(lines)


def _unique_sources(chunks):
    """Ordered, de-duplicated source filenames from the retrieved chunks.

    Computed from metadata so attribution is guaranteed correct rather than
    left to the LLM to produce.
    """
    seen = OrderedDict()
    for c in chunks:
        src = c.get("source", "unknown")
        seen[src] = None
    return list(seen.keys())


def ask(question, k=TOP_K):
    """Answer a question grounded in retrieved review chunks.

    Returns a dict: {"answer": str, "sources": list[str], "chunks": list}.
    """
    chunks = retrieve(question, k=k)

    # Pre-LLM grounding gate: if nothing retrieved well, refuse without calling
    # the model. This stops the LLM from ever seeing off-topic context it might
    # be tempted to answer from general knowledge.
    if not chunks or chunks[0]["distance"] > DISTANCE_CUTOFF:
        return {
            "answer": "I don't have enough information on that.",
            "sources": [],
            "chunks": chunks,
        }

    context = _format_context(chunks)
    user_msg = USER_TEMPLATE.format(context=context, question=question)

    client = Groq(api_key=os.environ["GROQ_API_KEY"])
    resp = client.chat.completions.create(
        model=MODEL,
        temperature=0,  # deterministic, reduces drift from context
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ],
    )
    answer = resp.choices[0].message.content.strip()

    # If the model refused, don't attach sources — nothing was actually used.
    refused = answer.lower().startswith("i don't have enough information")
    sources = [] if refused else _unique_sources(chunks)

    return {"answer": answer, "sources": sources, "chunks": chunks}


if __name__ == "__main__":
    # Manual end-to-end test, including one out-of-corpus question that should
    # trigger a refusal.
    tests = [
        "What do students say about Paul Hilfinger's lectures and projects in CS 61B?",
        "How do students describe John DeNero as a CS 61A instructor?",
        "What's the student consensus on Satish Rao's teaching style and exams?",
        "What is the meal plan price at the dining halls?",  # not in corpus -> refuse
    ]
    for q in tests:
        print("=" * 78)
        print("Q:", q)
        result = ask(q)
        print("\nANSWER:\n", result["answer"])
        print("\nSOURCES:", result["sources"])
        print("TOP DISTANCE:",
              round(result["chunks"][0]["distance"], 3) if result["chunks"] else "n/a")
        print()