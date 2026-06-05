"""
ingest.py — Load raw RMP review files and parse them into clean, structured reviews.

Each data/*.txt file is one professor's Rate My Professors page, copy-pasted as
plain text. The page has a consistent block structure per review:

    Quality
    <number>
    Difficulty
    <number>
    <course>            e.g. CS61B, 61A, Computer IconCS61A
    <date>              e.g. Dec 14th, 2022
    For Credit: ...     } zero or more metadata lines
    Attendance: ...     }
    Would Take Again:.. }
    Grade: ...          }
    Textbook: ...       }
    Online Class: ...   }
    <REVIEW TEXT>        <- the prose we actually want (1+ lines)
    <tag bubble>         } zero or more tag lines (e.g. "Tough grader")
    <tag bubble>         }
    Helpful              <- footer marker that ends every review
    Thumbs up
    <number>
    Thumbs down
    <number>

We walk the lines, detect each "Quality" marker as the start of a review, then
pull the prose that sits after the metadata block and before the Helpful footer.
Everything else (header, nav, ads, footer, rating distribution) is discarded
because it never sits inside a Quality...Helpful block.
"""

import os
import re
import json

DATA_DIR = "data"
RAW_OUT = "raw_documents.json"      # raw loaded text, before structured parsing
REVIEWS_OUT = "reviews.json"        # cleaned, structured reviews

# Lines that are metadata key/values, not review prose. If a line starts with
# one of these prefixes, it's structural and should be skipped, not treated as
# the review text.
META_PREFIXES = (
    "For Credit:", "Attendance:", "Would Take Again:", "Grade:",
    "Textbook:", "Online Class:",
)

# Known RMP tag bubbles. These appear AFTER the review prose. They're short,
# title-cased or all-caps phrases. We treat a line as a tag (not review prose)
# if it matches this set (case-insensitive). Keeping an explicit set is safer
# than guessing by capitalization, since real reviews can be short too.
TAG_BUBBLES = {
    "clear grading criteria", "inspirational", "group projects", "online savvy",
    "get ready to read", "respected", "hilarious", "caring", "tough grader",
    "extra credit", "lots of homework", "test heavy", "lecture heavy",
    "amazing lectures", "accessible outside class", "graded by few things",
    "gives good feedback", "skip class? you won't pass.", "would take again",
    "participation matters", "so many papers",
}


def load_raw_documents(data_dir=DATA_DIR):
    """Load every .txt file in data_dir. Returns {source_name: raw_text}."""
    docs = {}
    for fname in sorted(os.listdir(data_dir)):
        if not fname.endswith(".txt"):
            continue
        path = os.path.join(data_dir, fname)
        with open(path, "r", encoding="utf-8") as f:
            docs[fname] = f.read()
    return docs


def normalize_course(raw_course):
    """Strip junk like 'Computer Icon' prefix from a course token."""
    c = raw_course.replace("Computer Icon", "").strip()
    return c


def is_tag_line(line):
    return line.strip().lower() in TAG_BUBBLES


def parse_reviews(source_name, text):
    """Parse one professor's raw page text into a list of structured reviews."""
    lines = [ln.strip() for ln in text.splitlines()]
    reviews = []
    i = 0
    n = len(lines)

    while i < n:
        # A review starts at a "Quality" line immediately followed by a number.
        if lines[i] == "Quality" and i + 1 < n and re.match(r"^\d+(\.\d+)?$", lines[i + 1]):
            quality = float(lines[i + 1])
            j = i + 2

            # Expect "Difficulty" then a number next.
            difficulty = None
            if j < n and lines[j] == "Difficulty" and j + 1 < n and re.match(r"^\d+(\.\d+)?$", lines[j + 1]):
                difficulty = float(lines[j + 1])
                j += 2

            # Next non-empty line is the course token.
            while j < n and lines[j] == "":
                j += 1
            course = normalize_course(lines[j]) if j < n else ""
            j += 1

            # Next non-empty line is the date; skip it.
            while j < n and lines[j] == "":
                j += 1
            # date line (we don't need to keep it, just advance past it)
            if j < n:
                j += 1

            # Skip metadata lines (For Credit:, Grade:, etc.) and blanks.
            while j < n and (lines[j] == "" or lines[j].startswith(META_PREFIXES)):
                j += 1

            # Now collect review prose until we hit a tag bubble or "Helpful".
            prose_parts = []
            while j < n and lines[j] != "Helpful":
                line = lines[j]
                if line == "":
                    j += 1
                    continue
                if is_tag_line(line):
                    # Once tags start, prose is over. Skip remaining tags.
                    j += 1
                    continue
                # Stop if we somehow ran into the next review's start.
                if line == "Quality" and j + 1 < n and re.match(r"^\d+(\.\d+)?$", lines[j + 1]):
                    break
                prose_parts.append(line)
                j += 1

            review_text = " ".join(prose_parts).strip()

            # Only keep reviews that actually have prose. Drop "No Comments",
            # empty strings, and sub-15-char noise (e.g. "1337", ":)").
            if (review_text
                    and len(review_text) >= 15
                    and review_text.lower() not in ("no comments", "no comment")):
                reviews.append({
                    "source": source_name,
                    "course": course,
                    "quality": quality,
                    "difficulty": difficulty,
                    "text": review_text,
                })

            # Advance i to wherever we stopped.
            i = j
        else:
            i += 1

    return reviews


def main():
    raw_docs = load_raw_documents()
    print(f"Loaded {len(raw_docs)} raw document(s): {list(raw_docs.keys())}")

    with open(RAW_OUT, "w", encoding="utf-8") as f:
        json.dump(raw_docs, f, indent=2)

    all_reviews = []
    for source, text in raw_docs.items():
        reviews = parse_reviews(source, text)
        print(f"  {source}: parsed {len(reviews)} reviews")
        all_reviews.extend(reviews)

    with open(REVIEWS_OUT, "w", encoding="utf-8") as f:
        json.dump(all_reviews, f, indent=2)

    print(f"\nTotal reviews parsed: {len(all_reviews)}")
    print(f"Wrote {REVIEWS_OUT}\n")

    # --- Inspection: print a cleaned document sample (milestone requirement) ---
    print("=" * 70)
    print("SAMPLE: first 3 cleaned reviews (verify no nav/HTML/boilerplate)")
    print("=" * 70)
    for r in all_reviews[:3]:
        print(f"\n[{r['source']} | {r['course']} | Q={r['quality']} D={r['difficulty']}]")
        print(r["text"])


if __name__ == "__main__":
    main()
