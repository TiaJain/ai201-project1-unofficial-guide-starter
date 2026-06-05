"""
app.py — Gradio web interface for the Unofficial Guide to Berkeley CS professors.

Run:
    python app.py
Then open http://localhost:7860

Type a question about any of the 10 professors in the corpus and the system
retrieves relevant student reviews, answers strictly from them, and lists which
source files the answer drew on. Questions outside the corpus are declined.
"""

import gradio as gr

from query import ask

EXAMPLES = [
    "What do students say about Paul Hilfinger's lectures and projects in CS 61B?",
    "How do students describe John DeNero as a CS 61A instructor?",
    "What's the student consensus on Satish Rao's teaching style and exams?",
    "Do students find Babak Ayazifar's exams difficult, and would they recommend him?",
    "What do students say about Josh Hug's CS 61B lectures versus his exams?",
]


def handle_query(question):
    if not question or not question.strip():
        return "Please enter a question.", ""
    result = ask(question)
    answer = result["answer"]
    if result["sources"]:
        sources = "\n".join(f"• {s}" for s in result["sources"])
    else:
        sources = "(no sources — question not covered by the reviews)"
    return answer, sources


with gr.Blocks(title="Unofficial Guide: Berkeley CS Professors") as demo:
    gr.Markdown(
        "# Unofficial Guide: Berkeley CS Professors\n"
        "Ask about teaching style, exams, workload, or whether students recommend "
        "a professor. Answers come **only** from student reviews on Rate My "
        "Professors — if the reviews don't cover it, the system says so."
    )
    inp = gr.Textbox(
        label="Your question",
        placeholder="e.g. What do students say about Hilfinger's projects?",
    )
    btn = gr.Button("Ask", variant="primary")
    answer = gr.Textbox(label="Answer", lines=8)
    sources = gr.Textbox(label="Retrieved from", lines=4)

    btn.click(handle_query, inputs=inp, outputs=[answer, sources])
    inp.submit(handle_query, inputs=inp, outputs=[answer, sources])

    gr.Examples(examples=EXAMPLES, inputs=inp)


if __name__ == "__main__":
    demo.launch()