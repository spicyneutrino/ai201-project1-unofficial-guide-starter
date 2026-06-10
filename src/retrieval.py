"""Hybrid semantic + BM25 retrieval with metadata filters."""

import argparse
import sys
from pathlib import Path

import chromadb
from rank_bm25 import BM25Okapi

CHROMA_PATH = Path(__file__).resolve().parent.parent / "chroma_db"

COLLECTION_NAMES = {
    "fixed": "chunks_fixed",
    "paragraph": "chunks_paragraph",
}

_bm25_cache: dict[str, tuple[BM25Okapi, list[dict]]] = {}


def rrf_score(semantic_rank: int, bm25_rank: int, k: int = 60) -> float:
    return 1 / (k + semantic_rank) + 1 / (k + bm25_rank)


def build_where(subreddit_filter: list[str] | None, min_score: int) -> dict | None:
    clauses = []
    if subreddit_filter:
        clauses.append({"subreddit": {"$in": subreddit_filter}})
    if min_score > 0:
        clauses.append({"post_score": {"$gte": min_score}})
    if not clauses:
        return None
    if len(clauses) == 1:
        return clauses[0]
    return {"$and": clauses}


def get_client() -> chromadb.PersistentClient:
    return chromadb.PersistentClient(path=str(CHROMA_PATH))


def load_all_chunks(strategy: str) -> list[dict]:
    client = get_client()
    collection = client.get_collection(COLLECTION_NAMES[strategy])
    result = collection.get(include=["documents", "metadatas"])
    chunks = []
    for doc, meta, cid in zip(result["documents"], result["metadatas"], result["ids"]):
        chunk = dict(meta)
        chunk["text"] = doc
        chunk["id"] = cid
        chunks.append(chunk)
    return chunks


def get_bm25_index(strategy: str) -> tuple[BM25Okapi, list[dict]]:
    if strategy not in _bm25_cache:
        chunks = load_all_chunks(strategy)
        tokenized = [c["text"].lower().split() for c in chunks]
        _bm25_cache[strategy] = (BM25Okapi(tokenized), chunks)
    return _bm25_cache[strategy]


def semantic_search(query: str, strategy: str, k: int, where: dict | None) -> list[dict]:
    client = get_client()
    collection = client.get_collection(COLLECTION_NAMES[strategy])
    kwargs = {"query_texts": [query], "n_results": k, "include": ["documents", "metadatas", "distances"]}
    if where:
        kwargs["where"] = where
    result = collection.query(**kwargs)

    chunks = []
    for i, (doc, meta, dist) in enumerate(
        zip(result["documents"][0], result["metadatas"][0], result["distances"][0])
    ):
        chunk = dict(meta)
        chunk["text"] = doc
        chunk["semantic_rank"] = i
        chunk["semantic_distance"] = dist
        chunks.append(chunk)
    return chunks


def chunk_matches_where(chunk: dict, where: dict | None) -> bool:
    if not where:
        return True
    sub_filter = where.get("subreddit", {}).get("$in")
    if sub_filter and chunk["subreddit"] not in sub_filter:
        return False
    min_s = where.get("post_score", {}).get("$gte")
    if min_s is not None and chunk["post_score"] < min_s:
        return False
    if "$and" in where:
        return all(chunk_matches_where(chunk, clause) for clause in where["$and"])
    return True


def bm25_search(query: str, strategy: str, k: int, where: dict | None) -> list[dict]:
    _, all_chunks = get_bm25_index(strategy)
    corpus_chunks = [c for c in all_chunks if chunk_matches_where(c, where)]
    if not corpus_chunks:
        return []

    tokenized = [c["text"].lower().split() for c in corpus_chunks]
    bm25 = BM25Okapi(tokenized)
    scores = bm25.get_scores(query.lower().split())
    ranked_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:k]
    results = []
    for rank, idx in enumerate(ranked_indices):
        chunk = dict(corpus_chunks[idx])
        chunk["bm25_rank"] = rank
        results.append(chunk)
    return results


def chunk_key(chunk: dict) -> str:
    return f"{chunk['post_id']}_s{chunk['strategy'][0]}_c{chunk['chunk_index']}"


def merge_rrf(semantic: list[dict], bm25: list[dict], k: int) -> list[dict]:
    chunks_by_key: dict[str, dict] = {}
    sem_ranks = {chunk_key(c): i for i, c in enumerate(semantic)}
    bm25_ranks = {chunk_key(c): i for i, c in enumerate(bm25)}

    for chunk in semantic + bm25:
        chunks_by_key[chunk_key(chunk)] = chunk

    scores = {}
    for key in set(sem_ranks) | set(bm25_ranks):
        scores[key] = rrf_score(sem_ranks.get(key, 9999), bm25_ranks.get(key, 9999))

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:k]
    results = []
    for key, score in ranked:
        chunk = dict(chunks_by_key[key])
        chunk["retrieval_score"] = score
        results.append(chunk)
    return results


def retrieve(
    query: str,
    strategy: str = "fixed",
    k: int = 5,
    subreddit_filter: list[str] | None = None,
    min_score: int = 0,
    use_hybrid: bool = True,
) -> list[dict]:
    where = build_where(subreddit_filter, min_score)
    semantic = semantic_search(query, strategy, k, where)

    if not use_hybrid:
        for i, chunk in enumerate(semantic):
            chunk["retrieval_score"] = 1 / (60 + i)
        return semantic[:k]

    bm25 = bm25_search(query, strategy, k, where)
    return merge_rrf(semantic, bm25, k)


def run_tests() -> None:
    queries = [
        "How do I get a software engineering internship with no experience?",
        "How many LeetCode problems should I solve?",
        "What GPA is competitive for tech internships?",
    ]
    for q in queries:
        print(f"\nQuery: {q}")
        chunks = retrieve(q, strategy="fixed", k=3)
        for i, c in enumerate(chunks):
            print(f"  [{i+1}] score={c.get('retrieval_score', 0):.4f} r/{c['subreddit']} - {c['post_title'][:60]}")
            print(f"      {c['text'][:120]}...")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true")
    args = parser.parse_args()
    if args.test:
        run_tests()
