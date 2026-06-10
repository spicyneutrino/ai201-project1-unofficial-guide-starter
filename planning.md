# Project 1 Planning: The Unofficial Guide

> Write this document before you write any pipeline code.
> Your spec and architecture diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Update the Retrieval Approach and Chunking Strategy sections if you change your approach during implementation.
> Update this file before starting any stretch features.

---

## Domain

**CS Internship and Early Career Advice from Reddit**

This domain covers student-generated, community-validated advice about breaking into software engineering: finding and landing internships, preparing for technical interviews, navigating offers, and early career decisions. The knowledge is valuable because it reflects real, recent experiences from people who went through the process, not sanitized career center advice. It is hard to find through official channels because it is scattered across thousands of Reddit threads, ranked by community upvotes rather than indexed for search, and constantly updated as the job market shifts.

---

## Documents

Data is collected from 5 subreddits using the Reddit public JSON API. Each document is one Reddit post combined with its top comments (filtered by score >= 3, depth <= 2). Target: 2 posts per subreddit, 10 documents total. Raw JSON is saved to `data/raw/`; processed text is in `data/processed/`. Listing JSON files are stored in `data/raw/listings/` and are not processed by the pipeline.

| # | Source | Description | URL or location |
|---|--------|-------------|-----------------|
| 1 | r/cscareerquestions | 4 years at Big tech. Being likeable beats being productive every single time (score: 4990) | https://www.reddit.com/r/cscareerquestions/comments/1mrujpf/ |
| 2 | r/cscareerquestions | AWS Cloud Chief on replacing juniors with AI (score: 6899) | https://www.reddit.com/r/cscareerquestions/comments/1mvid8s/ |
| 3 | r/csMajors | Can't stop tearing up, got my first FAANG offer from Apple (score: 5752) | https://www.reddit.com/r/csMajors/comments/1locuwk/ |
| 4 | r/csMajors | My job search — 2000+ applications (score: 4408) | https://www.reddit.com/r/csMajors/comments/1nhwbhc/ |
| 5 | r/internships | Got sent a return offer by mistake LMAO (score: 852) | https://www.reddit.com/r/internships/comments/1nd2q9t/ |
| 6 | r/internships | Got caught sleeping with 2 days left on my internship (score: 1040) | https://www.reddit.com/r/internships/comments/1nkvb9v/ |
| 7 | r/leetcode | Got dumped by GF of 4 years but got a Meta offer today (score: 4485) | https://www.reddit.com/r/leetcode/comments/1ljvjh3/ |
| 8 | r/leetcode | it takes time — LeetCode grind and job market (score: 3939) | https://www.reddit.com/r/leetcode/comments/1nrwgv8/ |
| 9 | r/SoftwareEngineering | Our team stopped doing standups, story points and retros (score: 151) | https://www.reddit.com/r/SoftwareEngineering/comments/1rq16fl/ |
| 10 | r/SoftwareEngineering | How is your team reviewing all the AI generated code? (score: 74) | https://www.reddit.com/r/SoftwareEngineering/comments/1smr8bl/ |

Each processed document follows this format:

```
SUBREDDIT: cscareerquestions
POST_ID: 1mrujpf
POST_TITLE: <post title>
POST_SCORE: 4990
POST_URL: https://www.reddit.com/r/cscareerquestions/comments/1mrujpf/
POST_DATE: 2025-08-16

POST:
<post body text>

COMMENTS:
[score: 412] <comment text>
```

---

## Chunking Strategy

Two strategies are implemented and stored as separate ChromaDB collections (`chunks_fixed` and `chunks_paragraph`).

**Strategy A — Fixed character chunking (baseline)**

**Chunk size:** 500 characters

**Overlap:** 100 characters

**Reasoning:** Reddit comments are short and opinion-dense. A 500-character window captures roughly 2–4 short comments or one medium comment with context. The 100-character overlap prevents a key sentence from being split across two chunks where neither chunk is retrievable on its own. Chunks under 50 characters are discarded.

**Strategy B — Paragraph-based chunking (comparison)**

**Chunk size:** Split on `\n\n`; minimum 80 characters (merge shorter paragraphs), maximum 600 characters (split at sentence boundaries)

**Overlap:** None

**Reasoning:** Reddit posts and comments are already written in short paragraphs. Splitting at paragraph boundaries respects the author's semantic grouping. Chunks under 80 characters are discarded.

**Final chunk counts (10 documents):** 233 fixed, 416 paragraph.

---

## Retrieval Approach

**Embedding model:** `all-MiniLM-L6-v2` via `sentence-transformers` — runs locally, 384-dimensional embeddings, no API key, fast CPU inference.

**Top-k:** 5 — Reddit answers are often spread across multiple comments; k=3 risks missing high-signal chunks in positions 4–5.

**Vector store:** ChromaDB (local), two collections: `chunks_fixed` and `chunks_paragraph`.

**Hybrid search (stretch):** Semantic search (ChromaDB) combined with BM25 (`rank_bm25`) via Reciprocal Rank Fusion:

```
RRF_score(chunk) = 1/(60 + semantic_rank) + 1/(60 + bm25_rank)
```

**Metadata filtering (stretch):** Subreddit filter (`{"subreddit": {"$in": [...]}}`) and minimum post score (`{"post_score": {"$gte": N}}`).

**Production tradeoff reflection:**

If deploying this for real users, the factors I would weigh when choosing an embedding model:

- **Context length:** all-MiniLM-L6-v2 has a 256-token limit. A long Reddit post body gets silently truncated. For production, `all-mpnet-base-v2` (384 tokens) or an API model like `text-embedding-3-small` (8191 tokens) would handle longer documents without truncation risk.
- **Multilingual support:** not needed for this corpus, but for a broader student community, multilingual-e5 or a Cohere multilingual model would be necessary.
- **Local vs. API latency:** local models have zero marginal cost and no rate limits, which matters for a high-query system. API embeddings (OpenAI, Cohere) have better accuracy on domain-specific text but add latency, cost, and an external dependency.
- **Accuracy on informal text:** all-MiniLM-L6-v2 was trained on general web text and handles informal Reddit writing reasonably well. A fine-tuned model on forum or QA data (e.g., `multi-qa-MiniLM-L6-cos-v1`) would likely outperform it on this domain.

---

## Evaluation Plan

Questions were rewritten after scraping to match actual document content. All 5 are specific enough to judge correctness.

| # | Question | Expected answer |
|---|----------|-----------------|
| 1 | What do students say about the role of social skills vs technical skills in getting and keeping a tech job? | Social skills and likeability are cited as more important than raw productivity for job security and advancement at big tech. |
| 2 | What is the experience of preparing for and passing a Meta software engineering interview? | Extensive LeetCode practice (hundreds of problems), behavioral prep, and multiple interview rounds; the poster passed after a long grind and relationship difficulties. |
| 3 | How many job applications did students send before getting a software engineering offer? | Community reports range from hundreds to over 2000 applications; volume and persistence are recurring themes. |
| 4 | What do students say about getting a return offer after a summer internship? | Return offers can come through unexpected channels; one post describes receiving an offer erroneously then having it rescinded. |
| 5 | How are software engineering teams handling code review for AI-generated code? | Teams are struggling; common responses include stricter review processes, pair review, and skepticism about AI output quality. |

---

## Anticipated Challenges

1. **Retrieval returning advice from the wrong context.** A question about Meta interviews may retrieve an Apple FAANG offer post because both share "interview" and "offer" vocabulary. The embedding model may rank posts by title signals that do not reflect primary content (e.g., a breakup title masking interview prep content). Mitigation: subreddit filtering and content-summary metadata separate from Reddit titles.

2. **Key information split across chunk boundaries.** A post might introduce tips in one paragraph and list them in the next. If fixed chunking splits mid-thought, neither chunk retrieves well. The paragraph strategy reduces this but depends on consistent Reddit formatting.

3. **Noise in low-score comments.** Comments below score 3 are filtered, but low-effort comments can still clear that threshold on popular posts and retrieve on keyword overlap without useful advice.

4. **Reddit API rate limiting.** Mitigation: `time.sleep(1)` between scraper requests; raw JSON committed to repo so re-scraping is never needed during development.

---

## Architecture

```
+------------------+     +-------------------+     +------------------------+
|  Reddit JSON API |     |  Raw JSON Files   |     |  Cleaned Text Files    |
|  (scraper.py)    | --> |  data/raw/*.json  | --> |  data/processed/*.txt  |
+------------------+     +-------------------+     +------------------------+
                                                              |
                                              +--------------+--------------+
                                              |                             |
                                   +----------v---------+    +--------------v------+
                                   | Strategy A         |    | Strategy B          |
                                   | Fixed Char Chunks  |    | Paragraph Chunks    |
                                   | 500 chars, 100 ovr |    | split on \n\n       |
                                   +----------+---------+    +--------------+------+
                                              |                             |
                                              +-------------+---------------+
                                                            |
                                              +-------------v--------------+
                                              | Embedding                  |
                                              | all-MiniLM-L6-v2           |
                                              | (sentence-transformers)    |
                                              +-------------+--------------+
                                                            |
                                              +-------------v--------------+
                                              | Vector Store               |
                                              | ChromaDB (local)           |
                                              | collections: fixed,        |
                                              |   paragraph                |
                                              +-------------+--------------+
                                                            |
                                         +------------------+------------------+
                                         |                                     |
                              +----------v---------+               +-----------v--------+
                              | Semantic Retrieval |               | BM25 Retrieval     |
                              | ChromaDB query     |               | rank_bm25          |
                              | top-k = 5          |               | top-k = 5          |
                              +----------+---------+               +-----------+--------+
                                         |                                     |
                                         +------------------+------------------+
                                                            |
                                              +-------------v--------------+
                                              | Reciprocal Rank Fusion     |
                                              | (hybrid search)            |
                                              +-------------+--------------+
                                                            |
                                              +-------------v--------------+
                                              | Generation                 |
                                              | Groq llama-3.3-70b         |
                                              | Grounded prompt            |
                                              | Source attribution         |
                                              +-------------+--------------+
                                                            |
                                              +-------------v--------------+
                                              | Gradio Interface           |
                                              | app.py                     |
                                              +----------------------------+
```

---

## AI Tool Plan

**Milestone 3 — Ingestion and chunking:**

- *Tool:* Claude (Cursor agent)
- *Input:* Documents section, Reddit JSON structure, processed document format, chunking strategy (500/100 fixed, paragraph on `\n\n`)
- *Expected output:* `src/scraper.py`, `src/ingest.py`, `src/chunking.py`
- *Verification:* Run ingest on 10 raw JSON files; confirm headers parseable; run chunking and check chunk counts exceed 50 per collection

**Milestone 4 — Embedding and retrieval:**

- *Tool:* Claude (Cursor agent)
- *Input:* Retrieval approach section, RRF formula, metadata fields, ChromaDB collection names
- *Expected output:* `src/embed.py`, `src/retrieval.py` with hybrid search and metadata filters
- *Verification:* `embed.py` loads 233+ fixed and 416+ paragraph chunks; `retrieval.py --test` returns relevant chunks for eval queries

**Milestone 5 — Generation and interface:**

- *Tool:* Claude (Cursor agent)
- *Input:* Grounding requirement, exact system prompt, Gradio input/output spec, conversational memory cap of 3 turns
- *Expected output:* `src/generate.py`, `app.py`
- *Verification:* Out-of-scope query returns exact refusal string; in-scope queries include programmatic Sources line; Playwright UI tests in distrobox confirm end-to-end behavior

For each component I reviewed generated code before running it, verified it against this spec, and tested on real scraped data before wiring into the next stage.
