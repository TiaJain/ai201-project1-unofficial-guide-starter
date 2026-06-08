# The Unofficial Guide: Project 1

An unofficial guide to UC Berkeley CS professors, built from student reviews on Rate My Professors. You ask a question in plain language and the system answers using only what students actually wrote. It cites which review file the answer came from, and it declines when the reviews don't cover the topic.

---

## Domain

This system covers student reviews of UC Berkeley CS professors, sourced from Rate My Professors. This knowledge is valuable because it captures honest, experience based opinions about teaching quality, exam difficulty, and workload that don't show up in any official university channel. Official course catalogs and syllabi tell you what a class covers. They don't tell you whether a professor's lectures are worth attending, how curved the exams are, or whether students would take them again. The system answers questions like whether Hilfinger's projects are worth it, or whether Rao's teaching style is hit or miss, by pulling from many individual reviews. It also handles cases where the reviews disagree with each other.

---

## Document Sources

I used ten professors, one .txt file each, all collected from Rate My Professors. I copied them manually because RMP renders reviews with JavaScript and blocks automated scraping. Each file has every review that was on that professor's page when I collected it.

| #  | Source             | Type                | URL or file path |
|----|--------------------|---------------------|------------------|
| 1  | Rate My Professors | Reviews (.txt)      | `data/hilfinger.txt` https://www.ratemyprofessors.com/professor/226535 |
| 2  | Rate My Professors | Reviews (.txt)      | `data/sahai.txt` https://www.ratemyprofessors.com/professor/887794 |
| 3  | Rate My Professors | Reviews (.txt)      | `data/rao.txt` https://www.ratemyprofessors.com/professor/525740 |
| 4  | Rate My Professors | Reviews (.txt)      | `data/garcia.txt` https://www.ratemyprofessors.com/professor/142865 |
| 5  | Rate My Professors | Reviews (.txt)      | `data/lustig.txt` https://www.ratemyprofessors.com/professor/1774912 |
| 6  | Rate My Professors | Reviews (.txt)      | `data/denero.txt` https://www.ratemyprofessors.com/professor/1621181 |
| 7  | Rate My Professors | Reviews (.txt)      | `data/hug.txt` https://www.ratemyprofessors.com/professor/667663 |
| 8  | Rate My Professors | Reviews (.txt)      | `data/kao.txt` https://www.ratemyprofessors.com/professor/2804069 |
| 9  | Rate My Professors | Reviews (.txt)      | `data/ranade.txt` https://www.ratemyprofessors.com/professor/2369550 |
| 10 | Rate My Professors | Reviews (.txt)      | `data/ayazifar.txt` https://www.ratemyprofessors.com/professor/761773 |

Review counts per professor after cleaning: Ayazifar 102, DeNero 271, Garcia 179, Hilfinger 116, Hug 89, Kao 68, Lustig 23, Ranade 38, Rao 119, Sahai 72.

---

## Chunking Strategy

**Chunk size.** One review per chunk. There is no fixed character window. Each chunk is a single student's full review, with a short context line in front of it that reads `Review of Professor <Name> (<course>): <review text>`.

**Overlap.** None between reviews. There is a 50 character fallback overlap that only kicks in if a single review somehow goes over 600 characters, which basically never happens since RMP caps reviews around 350 characters.

**Preprocessing before chunking.** `ingest.py` parses the RMP block structure, which is very consistent. Every review goes Quality, then a number, then Difficulty, then a number, then the course, then the date, then metadata lines like For Credit, Attendance, Grade, and Textbook, then the actual review text, then optional tag bubbles, then a Helpful footer. The parser keeps only the review text plus the course and the quality and difficulty numbers as metadata. It strips out site navigation, ads, rating distributions, tag bubbles, and the Helpful and Thumbs footers. Reviews under 15 characters get dropped as noise. One of them was literally just "1337". That filter took the total from 1,116 parsed reviews down to 1,077 usable chunks.

**Why these choices fit my documents.** An RMP review is already a complete, self contained unit. It's one student giving one opinion in a few sentences. If I split a single review into smaller windows I'd be cutting one thought in half, and neither half would retrieve well on its own. Something like "Hilfinger's exams are" would land in one chunk and "based on lecture" in another. If I merged several reviews into one bigger chunk I'd be blending different students' opinions into one embedding, which waters down the signal so a specific query can't match cleanly. The context line in front of each chunk means even a really short review like "Incredible lecturer" still carries the professor and course with it. That was one of the missing attribution risks I called out in planning.md.

**Final chunk count.** 1,077 chunks across 10 professors.

---

## Embedding Model

**Model used.** I used `all-MiniLM-L6-v2` through `sentence-transformers`, stored in ChromaDB with cosine distance. It runs locally with no API key and no rate limits, so iterating was fast and free, and it's a good fit for short English text like reviews.

**Production tradeoff reflection.** `all-MiniLM-L6-v2` is fast and free but it has a short 256 token context window and it's trained on general English. That means it can underweight CS specific jargon, and as the failure case below shows, it can't really tell apart course tokens that look almost identical like CS70 and CS170. If I were deploying this for real users and cost wasn't a constraint, here's what I'd weigh. First is accuracy on domain specific text. A bigger hosted model like OpenAI's `text-embedding-3-large` or Cohere's `embed-v3` would do a better job separating similar looking course codes and professor nicknames. Second is latency. API embeddings add a network round trip versus running locally, which matters for an interactive UI. Third is context length. A bigger window would let me embed multi review context if I ever changed the chunking. Fourth is multilingual support, which doesn't matter here since RMP reviews are all in English, so I wouldn't pay for it. For this project the local model's speed and zero cost won out over its accuracy ceiling.

---

## Grounded Generation

**System prompt grounding instruction.** The model gets a system prompt that forces grounding instead of just suggesting it. The main rules are these. Answer only from the CONTEXT in the user message and treat it as the only source of truth. Don't use any outside knowledge about these professors, courses, or Berkeley, even if the model happens to know it. If the context isn't enough, respond with exactly "I don't have enough information on that." with no guessing and no padding. When reviews conflict, say so honestly, something like "reviews are split, some say X and others say Y", instead of picking a side. And attribute claims to what students say rather than stating them as fact. The model runs at `temperature=0` so it's deterministic. The full prompt lives in `query.py` as `SYSTEM_PROMPT`.

**How source attribution shows up in the response.** Attribution is done in code, not left to the LLM. After retrieval, `_unique_sources()` pulls the deduplicated source filenames from the retrieved chunks' metadata, and those come back as the `sources` list and show up in the "Retrieved from" box in the UI. So the citation is correct even if the model forgets to cite anything. There's also a grounding safeguard that runs before generation, which is a distance gate set at `DISTANCE_CUTOFF = 0.55`. If the closest retrieved chunk is farther than that, the system refuses right away without ever calling the LLM, so the model never even sees off topic context that it might be tempted to answer from training knowledge. On a refusal the sources list is emptied, since an answer with no real basis shouldn't cite anything.

---

## Evaluation Report

I ran all five questions through `query.py`. The responses below are summarized, and the full outputs are reproducible by running the system.

| # | Question | Expected answer | System response (summarized) | Retrieval quality | Response accuracy |
|---|----------|-----------------|------------------------------|-------------------|-------------------|
| 1 | What do students say about Paul Hilfinger's lectures and projects in CS 61B? | Lectures are widely called poor or confusing, he reads off slides. Projects are brutal but rewarding and grading is fair. | Says lectures are divisive, quotes "completely useless" and "reads off the slides" but also "fun to listen to", and that projects and assignments are "lengthy" and "very good for learning". Flags the lecture split correctly. Source hilfinger.txt, top distance 0.224. | Relevant | Accurate |
| 2 | How do students describe John DeNero as a CS 61A instructor? | Overwhelmingly positive. Passionate, caring, clear, well organized lecturer. | Describes him as a great lecturer who cares about students, is passionate, and explains clearly and amusingly. Notes "legend" and "love him". Source denero.txt, top distance 0.245. | Relevant | Accurate |
| 3 | What's the student consensus on Satish Rao's teaching style and exams in CS 170? | Mixed to negative on teaching, hard to follow, reads slides. Exams very hard. | Varies by run, see failure case. Retrieval pulls mostly CS70 chunks for this CS170 question, and the answer ranges from a blended CS70/CS170 summary to an honest "only one CS170 review" to a refusal. Source rao.txt when it answers. | Off target, 4 of 5 (or 5 of 5) chunks were CS70, not CS170. | Partially accurate / unstable |
| 4 | Do students find Babak Ayazifar's exams difficult, and would they recommend him? | Yes to both. Exams are very hard but he curves generously and is highly recommended. | Says exams are difficult, quotes "some of the hardest exams I've ever taken" and "quite tricky", but that he curves generously and tests are "always fair", and that reviews are overwhelmingly positive on recommending him. Source ayazifar.txt, top distance 0.156. | Relevant | Accurate |
| 5 | What do students say about Josh Hug's CS 61B lectures versus his exams and workload? | Lectures praised as clear and funny. Exams hard but fair. Workload heavy. | Says lectures are "super clear" and make hard structures simple, the class is "hard and time consuming" but "enjoyable and manageable", exams are "pretty fair", and projects are "rewarding". Source hug.txt, top distance 0.311. | Relevant | Accurate |

**Summary.** 4 of 5 accurate, 1 unstable. The unstable one is Rao in CS 170, and it's a retrieval side course confusion issue that I break down below. The short version is that retrieval consistently pulls mostly CS70 chunks for a CS170 question, and what the generator does with those wrong course chunks changes from run to run.

---

## Failure Case Analysis

**Question that failed.** Any question that asks about Satish Rao in CS 170 specifically. For example "What do students say about Satish Rao in CS 170?" or "What's the student consensus on Satish Rao's teaching style and exams in CS 170?".

**What the system returned.** This is the interesting part. The system does not fail the same way every time. I ran a few different phrasings of the CS 170 question and got three different behaviors. Sometimes it blended CS70 and CS170 reviews into one confident answer as if they were the same course. Sometimes it noticed only one of the retrieved reviews was actually CS170 and answered honestly that there's just one review. And sometimes the distance gate refused the question entirely with "I don't have enough information on that.". Same underlying question, three different surface outcomes depending on the exact wording and on the run.

The thing that does NOT change is retrieval. Underneath all three behaviors, retrieval keeps pulling mostly CS70 chunks for a CS170 question. Here's the deterministic breakdown across three phrasings:

```
"What is the student consensus on Satish Rao teaching style and exams in CS 170?"
   CS70   0.277      CS170  0.293      CS70   0.314      CS70   0.317      CS70   0.325
   -> CS170: 1/5

"What do students say about Satish Rao in CS 170?"
   CS70   0.288      CS70   0.315      CS70   0.317      CS61A  0.322      CS70   0.330
   -> CS170: 0/5

"How hard are Satish Rao exams in CS 170?"
   CS70   0.351      CS70   0.365      CS170  0.376      CS70   0.388      CS70   0.394
   -> CS170: 1/5
```

So in the best case only 1 of 5 retrieved chunks is actually CS170, and in one phrasing zero of them are. The course the user asked about is barely represented or missing entirely from what the system reads.

**Root cause, tied to a specific pipeline stage.** This is a retrieval and embedding failure, not a generation failure. The embedding model, `all-MiniLM-L6-v2`, maps "CS70" and "CS170" to almost the same spot in vector space. They're one character apart and the model has no special handling for course numbers, so similarity alone can't separate them. On top of that, Rao teaches both courses and the corpus has way more CS70 reviews for him than CS170 ones, so the nearest neighbors to a CS170 query end up being mostly CS70 chunks. The course number is sitting right there in each chunk's metadata, but retrieval only uses that metadata to display the course, not to filter on it. So nothing is actually forcing the results to match the course that was asked about. This is the same cross course contamination risk I predicted in the Anticipated Challenges section of planning.md.

The unstable surface behavior is a symptom of this. Because retrieval hands the generator a pile of mostly wrong course chunks, and because Groq's model is nondeterministic even at temperature 0, what the LLM does with that bad context varies run to run. So the real problem isn't any single bad answer, it's that the system is fragile on course specific questions and I can't even count on it failing consistently. That's worse than a predictable failure, because it means the answer quality depends on a coin flip on top of bad retrieval.

**What I would change to fix it.** Add metadata filtering to retrieval. ChromaDB supports a `where` clause, so if a query mentions a specific course I could parse out that course code and pass `where={"course": "CS170"}` to narrow the candidate set before ranking by similarity. A lighter version of this is hybrid retrieval, where I keep semantic search but boost or rerank chunks whose metadata course exactly matches the course I detect in the query. Either way I'd be using the course metadata that's already on every chunk but currently goes unused at retrieval time. Fixing retrieval also fixes the instability, because once the model is reading the right course's reviews the nondeterminism has a lot less room to swing the answer.

---

## Spec Reflection

**One way the spec helped me during implementation.** Writing the Anticipated Challenges section of planning.md before I built anything meant the Rao CS170 versus CS70 problem was something I'd already predicted, not a surprise. I had already reasoned that since all the documents are structurally similar CS professor reviews, a query about one course or professor could pull high similarity chunks about a different one. So during evaluation I knew to actually check the per chunk course breakdown instead of just trusting the answer because it sounded good. That's how I caught that the real issue was in retrieval and not in the wording of any one answer. The spec basically turned debugging into confirming a known risk, which made my failure analysis specific instead of vague.

**One way my implementation diverged from the spec, and why.** My original planning.md chunking strategy said roughly 400 character chunks with 50 character overlap. Once I actually read through the collected reviews I switched to one review per chunk with no overlap. The reason is that RMP reviews are already short, capped around 350 characters, and atomic, since each one is a single opinion. So a fixed 400 character window would either split a review in half or jam two unrelated ones together, and both of those hurt retrieval. One review per chunk just matches the natural unit of the data. I updated the chunking strategy section of planning.md to document this change and why I made it, like the milestone asks.

---

## AI Usage

**Instance 1, chunking strategy that I overrode after looking at the real data.**

- *What I gave the AI.* My chunking strategy section from planning.md, the original 400 character and 50 overlap plan, plus a sample of the raw scraped Hilfinger review text, and I asked it to build the ingestion and chunking pipeline.
- *What it produced.* A parser keyed to the RMP block structure plus a chunker. Once we looked at the output it was pretty clear the fixed character window was the wrong unit for this kind of data.
- *What I changed or overrode.* I overrode the 400 character window and went with one review per chunk after seeing how short and self contained the reviews are, and I updated planning.md to match. I also told it to add a minimum length filter to drop sub 15 character junk like "1337" after I spotted it in the parsed output, which moved the chunk count from 1,116 to 1,077.

**Instance 2, generation code that crashed on my actual retrieve() output.**

- *What I gave the AI.* I asked it to write the end to end `ask()` function and a Gradio UI that enforced grounding and source attribution, based on my grounding requirement from planning.md.
- *What it produced.* A `query.py` that assumed the retrieved chunks were nested dicts, so it was reaching for `chunk["metadata"]["source"]` and `chunk["document"]`. Running it immediately threw `KeyError: 'metadata'`, because my actual `retrieve.py` returns flat dicts with keys like `chunk["text"]`, `chunk["source"]`, `chunk["course"]`, and `chunk["distance"]`.
- *What I changed or overrode.* I ran the code, hit the crash, and gave it my real `retrieve.py` so the field accessors got rewritten to match my flat structure. This is a case where I didn't just take the generated code as is. Running it and debugging it against my own pipeline was the only way to catch it, and it's a good reminder that you have to test AI output instead of trusting it.

---

## How to Run

```bash
pip install -r requirements.txt

# 1. Parse raw reviews and chunk them
python3 ingest.py        # data/*.txt to reviews.json
python3 chunk.py         # reviews.json to chunks.json (1,077 chunks)

# 2. Embed and index
python3 embed.py         # builds ChromaDB index at ./chroma_db

# 3. Test retrieval and end to end generation
python3 retrieve.py      # prints top 5 chunks for the 5 eval questions
python3 query.py         # runs grounded generation on sample questions

# 4. Launch the UI
python3 app.py           # open http://localhost:7860
```

You need a `GROQ_API_KEY` in a `.env` file at the repo root for generation to work.