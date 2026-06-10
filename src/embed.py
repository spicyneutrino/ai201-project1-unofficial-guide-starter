"""Embed chunks and load into ChromaDB collections."""

import sys
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.chunking import chunk_document

PROCESSED_DIR = Path(__file__).resolve().parent.parent / "data" / "processed"
CHROMA_PATH = Path(__file__).resolve().parent.parent / "chroma_db"
BATCH_SIZE = 100
MODEL_NAME = "all-MiniLM-L6-v2"


def chunk_id(chunk: dict) -> str:
  strategy_letter = chunk["strategy"][0]
  return f"{chunk['post_id']}_s{strategy_letter}_c{chunk['chunk_index']}"


def embed_collection(client: chromadb.PersistentClient, name: str, chunks: list[dict], model: SentenceTransformer) -> None:
    collection = client.get_or_create_collection(name)
    if collection.count() >= len(chunks) and collection.count() > 0:
        print(f"Skipping {name}: already has {collection.count()} chunks")
        return

    if collection.count() > 0:
        collection.delete(where={"post_id": {"$ne": ""}})

    texts = [c["text"] for c in chunks]
    ids = [chunk_id(c) for c in chunks]
    metadatas = [
        {
            "subreddit": c["subreddit"],
            "post_id": c["post_id"],
            "post_title": c["post_title"],
            "post_score": c["post_score"],
            "post_url": c["post_url"],
            "chunk_index": c["chunk_index"],
            "strategy": c["strategy"],
            "source_file": c["source_file"],
        }
        for c in chunks
    ]

    for i in range(0, len(chunks), BATCH_SIZE):
        batch_texts = texts[i : i + BATCH_SIZE]
        batch_ids = ids[i : i + BATCH_SIZE]
        batch_meta = metadatas[i : i + BATCH_SIZE]
        embeddings = model.encode(batch_texts, batch_size=32, show_progress_bar=False)
        collection.add(
            ids=batch_ids,
            documents=batch_texts,
            embeddings=embeddings.tolist(),
            metadatas=batch_meta,
        )
        print(f"  Added batch {i // BATCH_SIZE + 1} to {name}")

    print(f"{name}: {collection.count()} chunks loaded")


def main() -> None:
    files = sorted(PROCESSED_DIR.glob("*.txt"))
    if not files:
        print("No processed files found.")
        return

    all_fixed: list[dict] = []
    all_paragraph: list[dict] = []
    for path in files:
        fixed, paragraph = chunk_document(path)
        all_fixed.extend(fixed)
        all_paragraph.extend(paragraph)

    print(f"Chunked {len(files)} documents: {len(all_fixed)} fixed, {len(all_paragraph)} paragraph")

    model = SentenceTransformer(MODEL_NAME)
    client = chromadb.PersistentClient(path=str(CHROMA_PATH))

    embed_collection(client, "chunks_fixed", all_fixed, model)
    embed_collection(client, "chunks_paragraph", all_paragraph, model)


if __name__ == "__main__":
    main()
