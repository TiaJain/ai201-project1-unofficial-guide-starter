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

**Chunk size:**

**Overlap:**

**Reasoning:**

---

## Retrieval Approach

<!-- Which embedding model are you using (e.g., all-MiniLM-L6-v2 via sentence-transformers)?
     How many chunks will you retrieve per query (top-k)?
     If you were deploying this for real users and cost wasn't a constraint, what tradeoffs
     would you weigh in choosing a different embedding model — context length, multilingual
     support, accuracy on domain-specific text, latency? -->

**Embedding model:**

**Top-k:**

**Production tradeoff reflection:**

---

## Evaluation Plan

<!-- List your 5 test questions with their expected correct answers.
     Questions should be specific enough that you can judge whether the system's response
     is right or wrong. "What are good dining halls?" is too vague.
     "What do students say about wait times at [dining hall name] during lunch?" is testable. -->

| # | Question | Expected answer |
|---|----------|-----------------|
| 1 | | |
| 2 | | |
| 3 | | |
| 4 | | |
| 5 | | |

---

## Anticipated Challenges

<!-- What could go wrong? Name at least two specific risks with reasoning.
     Consider: noisy or inconsistent documents, missing source attribution, off-topic
     retrieval, chunks that split key information across boundaries. -->

1.

2.

---

## Architecture

<!-- Draw a diagram of your pipeline showing the five stages:
     Document Ingestion → Chunking → Embedding + Vector Store → Retrieval → Generation
     Label each stage with the tool or library you're using.
     You can use ASCII art, a Mermaid diagram, or embed a sketch as an image.
     You'll use this diagram as context when prompting AI tools to implement each stage. -->

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

**Milestone 3 — Ingestion and chunking:**

**Milestone 4 — Embedding and retrieval:**

**Milestone 5 — Generation and interface:**
