"""Grounded answer generation via Groq with source attribution."""

import os
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

SYSTEM_PROMPT = """You are a helpful assistant answering questions about CS internships and early career advice.
Answer the user's question using ONLY the information provided in the context below.
Do not use any knowledge from your training data.
If the provided context does not contain enough information to answer the question, respond with exactly:
"I don't have enough information in my documents to answer that question."
Always cite your sources at the end of your response using the format:
Sources: [post title] (r/subreddit)"""

FALLBACK = "I don't have enough information in my documents to answer that question."
MODEL = "llama-3.3-70b-versatile"
MAX_HISTORY_MESSAGES = 6


def format_context(chunks: list[dict]) -> str:
    parts = []
    for i, chunk in enumerate(chunks, 1):
        parts.append(
            f"[Document {i} — {chunk['post_title']} from r/{chunk['subreddit']}]\n{chunk['text']}"
        )
    return "\n\n".join(parts)


def build_sources_line(chunks: list[dict]) -> str:
    seen = set()
    sources = []
    for chunk in chunks:
        key = (chunk["post_title"], chunk["subreddit"])
        if key not in seen:
            seen.add(key)
            sources.append(f"[{chunk['post_title']}] (r/{chunk['subreddit']})")
    return "Sources: " + ", ".join(sources)


def generate_answer(
    query: str,
    chunks: list[dict],
    history: list[dict] | None = None,
) -> tuple[str, str]:
    sources = build_sources_line(chunks) if chunks else "Sources: (none)"

    if not chunks:
        return FALLBACK, sources

    context = format_context(chunks)
    user_content = f"Context:\n{context}\n\nQuestion: {query}"

    messages: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]
    if history:
        messages.extend(history[-MAX_HISTORY_MESSAGES:])
    messages.append({"role": "user", "content": user_content})

    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=0.2,
    )
    answer = response.choices[0].message.content.strip()

    if FALLBACK.lower() not in answer.lower():
        if "Sources:" not in answer:
            answer = f"{answer}\n\n{sources}"
    else:
        answer = FALLBACK

    return answer, sources
