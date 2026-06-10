"""Gradio interface for the Unofficial Guide RAG system."""

import gradio as gr

from src.generate import generate_answer
from src.retrieval import retrieve

SUBREDDITS = [
    "cscareerquestions",
    "csMajors",
    "leetcode",
    "internships",
    "softwareengineering",
]
MAX_TURNS = 3


def format_chunks_debug(chunks: list[dict]) -> str:
    if not chunks:
        return "(no chunks retrieved)"
    lines = []
    for i, c in enumerate(chunks, 1):
        preview = c["text"][:200].replace("\n", " ")
        lines.append(
            f"[{i}] score={c.get('retrieval_score', 0):.4f} | r/{c['subreddit']} | {c['post_title']}\n  {preview}..."
        )
    return "\n\n".join(lines)


def update_history(history: list[dict], query: str, answer: str) -> list[dict]:
    history = list(history or [])
    history.append({"role": "user", "content": query})
    history.append({"role": "assistant", "content": answer})
    return history[-(MAX_TURNS * 2) :]


def handle_query(query, subreddit_filter, min_score, strategy, use_hybrid, history):
    if not query or not query.strip():
        return "", "", "(enter a question)", history or []

    chunks = retrieve(
        query.strip(),
        strategy=strategy,
        k=5,
        subreddit_filter=subreddit_filter if subreddit_filter else None,
        min_score=int(min_score),
        use_hybrid=use_hybrid,
    )
    answer, sources = generate_answer(query.strip(), chunks, history)
    debug = format_chunks_debug(chunks)
    history = update_history(history, query.strip(), answer)
    return answer, sources, debug, history


def build_app() -> gr.Blocks:
    with gr.Blocks(title="The Unofficial Guide") as demo:
        gr.Markdown("# The Unofficial Guide\nAsk questions about CS internships and early career advice from Reddit.")

        history = gr.State([])

        with gr.Row():
            with gr.Column():
                query = gr.Textbox(label="Your question", lines=2)
                subreddit_filter = gr.CheckboxGroup(
                    choices=SUBREDDITS,
                    label="Filter by subreddit (leave blank for all)",
                )
                min_score = gr.Slider(0, 1000, step=50, value=0, label="Minimum post score")
                strategy = gr.Radio(["fixed", "paragraph"], value="fixed", label="Chunking strategy")
                use_hybrid = gr.Checkbox(value=True, label="Use hybrid search (BM25 + semantic)")
                submit_btn = gr.Button("Ask", variant="primary")

            with gr.Column():
                answer = gr.Textbox(label="Answer", lines=10)
                sources = gr.Textbox(label="Sources", lines=5)
                retrieved_chunks = gr.Textbox(label="Retrieved chunks (debug)", lines=8)

        outputs = [answer, sources, retrieved_chunks, history]
        submit_btn.click(
            handle_query,
            inputs=[query, subreddit_filter, min_score, strategy, use_hybrid, history],
            outputs=outputs,
        )
        query.submit(
            handle_query,
            inputs=[query, subreddit_filter, min_score, strategy, use_hybrid, history],
            outputs=outputs,
        )

    return demo


if __name__ == "__main__":
    build_app().launch(server_name="0.0.0.0", server_port=7860)
