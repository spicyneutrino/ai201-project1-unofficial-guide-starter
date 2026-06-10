"""Chunk processed documents using fixed-char and paragraph strategies."""

import re
from pathlib import Path

PROCESSED_DIR = Path(__file__).resolve().parent.parent / "data" / "processed"

HEADER_FIELDS = {
    "SUBREDDIT": "subreddit",
    "POST_ID": "post_id",
    "POST_TITLE": "post_title",
    "POST_SCORE": "post_score",
    "POST_URL": "post_url",
    "POST_DATE": "post_date",
}


def parse_document_header(text: str) -> tuple[dict, str]:
    lines = text.splitlines()
    metadata: dict = {}
    body_start = 0

    for i, line in enumerate(lines):
        if not line.strip():
            body_start = i + 1
            break
        if ":" in line:
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()
            if key in HEADER_FIELDS:
                field = HEADER_FIELDS[key]
                metadata[field] = int(value) if field == "post_score" else value

    body = "\n".join(lines[body_start:]).strip()
    if body.startswith("POST:"):
        body = body[len("POST:") :].strip()
    return metadata, body


def make_chunk(metadata: dict, text: str, chunk_index: int, strategy: str, source_file: str) -> dict:
    return {
        "text": text,
        "chunk_index": chunk_index,
        "source_file": source_file,
        "subreddit": metadata["subreddit"],
        "post_id": metadata["post_id"],
        "post_title": metadata["post_title"],
        "post_score": metadata["post_score"],
        "post_url": metadata["post_url"],
        "strategy": strategy,
    }


def chunk_fixed(
    body: str,
    metadata: dict,
    source_file: str,
    chunk_size: int = 500,
    overlap: int = 100,
) -> list[dict]:
    chunks: list[dict] = []
    start = 0
    chunk_index = 0
    while start < len(body):
        end = start + chunk_size
        text = body[start:end].strip()
        if len(text) >= 50:
            chunks.append(make_chunk(metadata, text, chunk_index, "fixed", source_file))
            chunk_index += 1
        if end >= len(body):
            break
        start = end - overlap
    return chunks


def split_long_paragraph(paragraph: str, max_len: int = 600) -> list[str]:
    if len(paragraph) <= max_len:
        return [paragraph]
    parts = re.split(r"(?<=[.!?])\s+", paragraph)
    result: list[str] = []
    current = ""
    for part in parts:
        candidate = f"{current} {part}".strip() if current else part
        if len(candidate) <= max_len:
            current = candidate
        else:
            if current:
                result.append(current)
            current = part
    if current:
        result.append(current)
    return result


def chunk_paragraph(
    body: str,
    metadata: dict,
    source_file: str,
    min_len: int = 80,
    max_len: int = 600,
) -> list[dict]:
    paragraphs = [p.strip() for p in body.split("\n\n") if p.strip()]
    merged: list[str] = []
    buffer = ""
    for para in paragraphs:
        for piece in split_long_paragraph(para, max_len):
            if buffer and len(buffer) + len(piece) + 2 < min_len:
                buffer = f"{buffer}\n\n{piece}"
            elif buffer:
                merged.append(buffer)
                buffer = piece
            else:
                buffer = piece
    if buffer:
        merged.append(buffer)

    chunks: list[dict] = []
    for i, text in enumerate(merged):
        text = text.strip()
        if len(text) >= min_len:
            chunks.append(make_chunk(metadata, text, i, "paragraph", source_file))
    return chunks


def chunk_document(filepath: str | Path) -> tuple[list[dict], list[dict]]:
    path = Path(filepath)
    text = path.read_text(encoding="utf-8")
    metadata, body = parse_document_header(text)
    source_file = path.name
    fixed = chunk_fixed(body, metadata, source_file)
    paragraph = chunk_paragraph(body, metadata, source_file)
    return fixed, paragraph


def main() -> None:
    files = sorted(PROCESSED_DIR.glob("*.txt"))
    total_fixed = total_para = 0
    for path in files:
        fixed, paragraph = chunk_document(path)
        total_fixed += len(fixed)
        total_para += len(paragraph)
        print(f"{path.name}: {len(fixed)} fixed, {len(paragraph)} paragraph chunks")
    print(f"Total: {total_fixed} fixed, {total_para} paragraph chunks")


if __name__ == "__main__":
    main()
