# Project 1 Planning: The Unofficial Guide

> Write this document before you write any pipeline code.
> Your spec and architecture diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Update the Retrieval Approach and Chunking Strategy sections if you change your approach during implementation.
> Update this file before starting any stretch features.

---

## Domain

Student reviews of UC Berkeley CS professors, sourced from Rate My Professors. This knowledge is valuable because it captures honest, experience-based opinions about teaching quality, exam difficulty, and workload that don't appear in any official university channel. Official course catalogs and syllabi tell you what a class covers- they don't tell you whether the professor's lectures are worth attending or how curved the exams are.

## Documents

| # | Source | Description | URL or location |
|---|--------|-------------|-----------------|
| 1 | Rate My Professors | Paul Hilfinger reviews | https://www.ratemyprofessors.com/professor/226535 |
| 2 | Rate My Professors | Anant Sahai reviews | https://www.ratemyprofessors.com/professor/887794 |
| 3 | Rate My Professors | Satish Rao reviews | https://www.ratemyprofessors.com/professor/525740 |
| 4 | Rate My Professors | Dan Garcia reviews | https://www.ratemyprofessors.com/professor/142865 |
| 5 | Rate My Professors | Michael (Miki) Lustig reviews | https://www.ratemyprofessors.com/professor/1774912 |
| 6 | Rate My Professors | John DeNero reviews | https://www.ratemyprofessors.com/professor/1621181 |
| 7 | Rate My Professors | Josh Hug reviews | https://www.ratemyprofessors.com/professor/667663 |
| 8 | Rate My Professors | Peyrin Kao reviews | https://www.ratemyprofessors.com/professor/2804069 |
| 9 | Rate My Professors | Gireeja Ranade reviews | https://www.ratemyprofessors.com/professor/2369550 |
| 10 | Rate My Professors | Babak Ayazifar reviews | https://www.ratemyprofessors.com/professor/761773 |

---

## Chunking Strategy

<!-- How will you split documents into chunks?
     State your chunk size (in tokens or characters), overlap size, and explain why those
     numbers fit the structure of your documents.
     A review-heavy corpus warrants different chunking than a long FAQ. -->

**Chunk size:** ~400 characters (roughly 80–100 tokens)

**Overlap:** 50 characters

**Reasoning:** Rate my professor reviews are pretty short, self contained opinions. typically 1–4 sentences each. One review usually expresses one coherent take (for ex: "exams are curved, attend lecture"). A 400 character chunk fits roughly one full review, so each embedding captures a complete thought that can stand alone in retrieval. going smaller (eg 200 chars) would split a single review midthought, so "Hilfinger's exams are" and "heavily based on lecture" land in separate chunks and neither is retrievable on its own. Going much larger would merge several unrelated reviews into one embedding, diluting the semantic signal so specific queries can't match precisely. the small 50 char overlap is a safety margin for reviews that run slightly long, so a fact spanning a boundary still appears intact in one chunk.

---

## Retrieval Approach

<!-- Which embedding model are you using (e.g., all-MiniLM-L6-v2 via sentence-transformers)?
     How many chunks will you retrieve per query (top-k)?
     If you were deploying this for real users and cost wasn't a constraint, what tradeoffs
     would you weigh in choosing a different embedding model — context length, multilingual
     support, accuracy on domain-specific text, latency? -->

**Embedding model:** all-MiniLM-L6-v2 via sentence-transformers (runs locally, no API key or rate limits)

**Top-k:** 5

**Production tradeoff reflection:** all-MiniLM-L6-v2 is fast and free but has a short 256-token context window and is trained on general English so it may underweight CS-specific jargon and professor nicknames. If cost weren't a constraint, I'd weigh: 
(1) a larger model like OpenAI text-embedding-3-large or Cohere embed-v3 for better accuracy on domain-specific text and longer context
(2) latency bc API embeddings add round-trip time (vs. local inference)
(3) domain adaptation, fine-tuning or a model trained on academic/review text would handle slang like "the curve is generous" better

---

## Evaluation Plan

<!-- List your 5 test questions with their expected correct answers.
     Questions should be specific enough that you can judge whether the system's response
     is right or wrong. "What are good dining halls?" is too vague.
     "What do students say about wait times at [dining hall name] during lunch?" is testable. -->

| # | Question | Expected answer |
|---|----------|-----------------|
| 1 | What do students say about Paul Hilfinger's lectures and projects in CS 61B? | Students consistently say his lectures are poor or confusing (he reads off slides and demos often break) and many recommend watching other professors' videos instead. The projects (e.g. Gitlet) are described as brutal and time-consuming but rewarding, and the grading is praised as fair: do the projects well and you can get an A even with mediocre exam scores. |
| 2 | How do students describe John DeNero as a CS 61A instructor? | Overwhelmingly positive. Students call him passionate, accessible (his "dog office hours" come up), and an excellent, well-organized lecturer. His exams are tough but doable, and reviewers note he cares about learning over grades. He won the 2018 Distinguished Teaching Award. |
| 3 | What's the student consensus on Satish Rao's teaching style and exams in CS 170? | Mixed-to-negative on teaching: many say his lectures are hard to follow and he reads slides without explanation, so you largely learn the material yourself. Exams are described as very hard, though some say grading was fair and TAs were responsive. |
| 4 | Do students find Babak Ayazifar's exams difficult, and would they recommend him? | Yes to both. Students describe his exams as really hard (either due to time crunch or material difficulty) but note the "clobber policy" softens the impact. Despite this he's very highly regarded; reviewers call him caring and recommend taking EECS 16A with him. 82% would take again. |
| 5 | What do students say about Josh Hug's CS 61B lectures versus his exams and workload? | Lectures are praised as amazing, clear, and funny, and a strong foundation for later CS classes. But students warn the exams are very hard and the workload is heavy, so you have to work hard. He won the 2023 Distinguished Teaching Award. |

---

## Anticipated Challenges

<!-- What could go wrong? Name at least two specific risks with reasoning.
     Consider: noisy or inconsistent documents, missing source attribution, off-topic
     retrieval, chunks that split key information across boundaries. -->

1. **Inconsistent / noisy review text:** RMP reviews use slang, abbreviations, and sometimes refer to professors by nickname or just "he/she." A query using the professor's full name may not semantically match a review that never names them, causing retrieval to miss relevant chunks.

2. **Cross-professor contamination:** Since all documents are structurally similar (CS professor reviews), a query about one professor may retrieve high-similarity chunks about a *different* professor who teaches the same course, producing an answer attributed to the wrong person. Source metadata helps attribution but won't stop the wrong chunk from being retrieved.

---

## Architecture

<!-- Draw a diagram of your pipeline showing the five stages:
     Document Ingestion → Chunking → Embedding + Vector Store → Retrieval → Generation
     Label each stage with the tool or library you're using.
     You can use ASCII art, a Mermaid diagram, or embed a sketch as an image.
     You'll use this diagram as context when prompting AI tools to implement each stage. -->

Document Ingestion        Chunking            Embedding + Vector Store      Retrieval              Generation
(Python, .txt files)  →   (custom chunk_text,  →  (all-MiniLM-L6-v2      →   (top-5 semantic    →   (Groq
 data/*.txt               ~400 char, 50 overlap)   → ChromaDB)               similarity search)     llama-3.3-70b-versatile)

---

## AI Tool Plan

<!-- For each part of the pipeline below, describe:
     - Which AI tool you plan to use (Claude, Copilot, ChatGPT, etc.)
     - What you'll give it as input (which sections of this planning.md, which requirements)
     - What you expect it to produce
     - How you'll verify the output matches your spec

     "I'll use AI to help me code" is not a plan.
     "I'll give Claude my Chunking Strategy section and ask it to implement chunk_text()
     with my specified chunk size and overlap" is a plan. -->

**Milestone 3 — Ingestion and chunking:** I'll give Claude my Documents and Chunking Strategy sections plus the architecture diagram, and ask it to implement a script that loads each data/*.txt file, strips leftover RMP boilerplate (ratings labels, "Would take again" tags), and produces ~400-char chunks with 50-char overlap, attaching the source filename as metadata to each chunk. I'll verify by printing 5 chunks and checking each is one readable, self-contained review.

**Milestone 4 — Embedding and retrieval:** I'll give Claude my Retrieval Approach section and ask it to embed chunks with all-MiniLM-L6-v2, store them in ChromaDB with source metadata, and write a retrieve(query, k=5) function returning chunks + distance scores. I'll verify by running 3 eval questions and checking distance scores are below 0.5 and chunks are on-topic.

**Milestone 5 — Generation and interface:** I'll give Claude my grounding requirement (answer only from retrieved chunks, cite source, refuse if not covered) and ask it to write the Groq prompt template and a Gradio UI matching the skeleton in the instructions. I'll verify by asking an out-of-scope question and confirming the system refuses instead of using general knowledge.
