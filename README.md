# The Unofficial Guide — Project 1

A RAG system that makes CS internship and early career advice from Reddit searchable and answerable. Ask a plain-language question and get a grounded, cited answer drawn from real Reddit posts and comments.

---

## Domain and Document Sources

### Domain

CS internship and early career advice from Reddit. This covers student-generated, community-validated guidance about breaking into software engineering: job search grind, interview prep, internship experiences, team culture, and early career decisions. The knowledge is valuable because it reflects real, recent experiences from people who went through the process — not sanitized career center advice. It is hard to find through official channels because it is scattered across thousands of Reddit threads, ranked by upvotes rather than indexed for search.

### Document Sources

10 documents collected from 5 subreddits via the Reddit public JSON API. Raw JSON is in `data/raw/`; processed text is in `data/processed/`.

| # | Subreddit | Post Title | Post URL | Score |
|---|-----------|------------|----------|-------|
| 1 | r/cscareerquestions | 4 years at Big tech. Being likeable beats being productive every single time | https://www.reddit.com/r/cscareerquestions/comments/1mrujpf/ | 4990 |
| 2 | r/cscareerquestions | [Breaking] AWS Cloud Chief says "replacing junior employees with AI is one of the dumbest things I've ever heard". The tide is shifting back. | https://www.reddit.com/r/cscareerquestions/comments/1mvid8s/ | 6899 |
| 3 | r/csMajors | Can't stop tearing up, got my first FAANG offer from Apple | https://www.reddit.com/r/csMajors/comments/1locuwk/ | 5752 |
| 4 | r/csMajors | My job search | https://www.reddit.com/r/csMajors/comments/1nhwbhc/ | 4408 |
| 5 | r/internships | Got sent a return offer by mistake LMAO | https://www.reddit.com/r/internships/comments/1nd2q9t/ | 852 |
| 6 | r/internships | Got caught sleeping with 2 days left on my internship. | https://www.reddit.com/r/internships/comments/1nkvb9v/ | 1040 |
| 7 | r/leetcode | Got dumped by GF of 4 years but got a Meta offer today | https://www.reddit.com/r/leetcode/comments/1ljvjh3/ | 4485 |
| 8 | r/leetcode | it takes time | https://www.reddit.com/r/leetcode/comments/1nrwgv8/ | 3939 |
| 9 | r/SoftwareEngineering | Our team stopped doing standups, story points and retros — and nothing broke | https://www.reddit.com/r/SoftwareEngineering/comments/1rq16fl/ | 151 |
| 10 | r/SoftwareEngineering | How is your team reviewing all the AI generated code? | https://www.reddit.com/r/SoftwareEngineering/comments/1smr8bl/ | 74 |

---

## Chunking Strategy

Two strategies are implemented in `src/chunking.py` and stored as separate ChromaDB collections.

**Strategy A — Fixed character chunking (baseline)**
- Chunk size: 500 characters
- Overlap: 100 characters
- Minimum chunk length: 50 characters (shorter chunks discarded)
- Rationale: A 500-character window captures roughly 2–4 short Reddit comments or one medium comment with context. Overlap prevents a key sentence from being split across two unreachable chunks.

**Strategy B — Paragraph-based chunking**
- Split on double newlines (`\n\n`)
- Minimum chunk size: 80 characters (adjacent short paragraphs merged)
- Maximum chunk size: 600 characters (long paragraphs split at sentence boundaries)
- Rationale: Reddit posts and comments are already written in short paragraphs. Splitting at paragraph boundaries respects the author's semantic grouping.

**Final chunk counts:** 233 fixed, 416 paragraph (across 10 documents).

### Sample Chunks

**Sample 1 (fixed)** — source: `SoftwareEngineering_1rq16fl.txt`

```
I have a hypothesis that many of the processes we run in engineering teams are mostly organizational theater.

Daily standups, story points, sprint planning, retrospectives, team metrics — the whole agile ceremony package.

A few years ago I accidentally tested this.

I became a tech lead of a brand new team and we started from scratch. Instead of introducing all the usual processes, we tried some
```

**Sample 2 (paragraph)** — source: `SoftwareEngineering_1rq16fl.txt`

```
I have a hypothesis that many of the processes we run in engineering teams are mostly organizational theater.
```

**Sample 3 (fixed)** — source: `SoftwareEngineering_1smr8bl.txt`

```
Our team typically spends 30-60 mins a day reviewing all production code before merging. This worked fine when humans wrote the code. We recently got Claude licenses and we’re now making PRs faster than anyone wants to review it and it’s causing pushback on using AI because it’s too much code to review. I’m sensing philosophical and cultural battles ahead. 

How has your team dealt with the increa
```

**Sample 4 (paragraph)** — source: `SoftwareEngineering_1smr8bl.txt`

```
Our team typically spends 30-60 mins a day reviewing all production code before merging. This worked fine when humans wrote the code. We recently got Claude licenses and we’re now making PRs faster than anyone wants to review it and it’s causing pushback on using AI because it’s too much code to review. I’m sensing philosophical and cultural battles ahead.
```

**Sample 5 (fixed)** — source: `csMajors_1locuwk.txt`

```
ven knows what CS is. I don't think they have even heard about ChatGPT. The school I went to isn't an ivy or a top 10, I'm from a college you've probably never even heard of.

And I just got into Apple...

All this to say, I have zero high level connections in the industry or any insider info about how to land in FAANG. I just grinded nonstop for many months, didn't give up, and with a little bit 
```

### Which Strategy Performed Better

**Paragraph chunking performed better overall** (4/5 accurate vs 3/5 for fixed). Paragraph chunks preserve complete semantic units — especially on longer posts like the Meta interview thread — so retrieval ranked the Meta post 2nd–3rd instead of 3rd only. Fixed chunking won on Q1 (social skills) where all top chunks came from one highly relevant post regardless of strategy. Paragraph is the better default for this corpus of long, comment-heavy Reddit threads.

---

## Embedding Model

**Model used:** `all-MiniLM-L6-v2` via `sentence-transformers` (384-dimensional embeddings, local CPU inference, no API key).

**Production tradeoff reflection:**

If deploying this for real users, the factors I would weigh when choosing an embedding model:

- **Context length:** all-MiniLM-L6-v2 has a 256-token limit. A long Reddit post body gets silently truncated. For production, `all-mpnet-base-v2` (384 tokens) or an API model like `text-embedding-3-small` (8191 tokens) would handle longer documents without truncation risk.
- **Multilingual support:** not needed for this corpus, but for a broader student community, multilingual-e5 or a Cohere multilingual model would be necessary.
- **Local vs. API latency:** local models have zero marginal cost and no rate limits, which matters for a high-query system. API embeddings (OpenAI, Cohere) have better accuracy on domain-specific text but add latency, cost, and an external dependency.
- **Accuracy on informal text:** all-MiniLM-L6-v2 was trained on general web text and handles informal Reddit writing reasonably well. A fine-tuned model on forum or QA data (e.g., `multi-qa-MiniLM-L6-cos-v1`) would likely outperform it on this domain.

---

## Retrieval Test Results

Retrieval combines **semantic search** (ChromaDB cosine similarity) with **BM25 keyword search** (`rank_bm25`) using **Reciprocal Rank Fusion (RRF)**:

```
RRF_score(chunk) = 1/(60 + semantic_rank) + 1/(60 + bm25_rank)
```

Top-k from each method are merged by chunk ID and re-ranked by combined RRF score. Default k=5.

### Query 1: Social skills vs technical skills

| Rank | Subreddit | Post Title | RRF |
|------|-----------|------------|-----|
| 1 | r/cscareerquestions | 4 years at Big tech. Being likeable beats being productive every single time | 0.0331 |
| 2 | r/cscareerquestions | 4 years at Big tech. Being likeable beats being productive every single time | 0.0328 |
| 3 | r/cscareerquestions | 4 years at Big tech. Being likeable beats being productive every single time | 0.0165 |

**Relevance:** All three chunks come from the same post whose title and body directly argue that likeability beats productivity at big tech — a direct match to the query about social vs technical skills.

### Query 2: Job application volume

| Rank | Subreddit | Post Title | RRF |
|------|-----------|------------|-----|
| 1 | r/csMajors | My job search | 0.0168 |
| 2 | r/csMajors | My job search | 0.0168 |
| 3 | r/csMajors | My job search | 0.0165 |

**Relevance:** All three chunks are from the "My job search" post where the author and commenters discuss sending over 2000 applications — directly answering the query about application volume.

### Query 3: AI code review

| Rank | Subreddit | Post Title | RRF |
|------|-----------|------------|-----|
| 1 | r/SoftwareEngineering | How is your team reviewing all the AI generated code? | 0.0331 |
| 2 | r/SoftwareEngineering | How is your team reviewing all the AI generated code? | 0.0168 |
| 3 | r/cscareerquestions | 4 years at Big tech. Being likeable beats being productive every single time | 0.0165 |

Top two chunks are from the post explicitly asking how teams review AI-generated code, including discussion of review burden and pushback when PR volume exceeds review capacity.

---

## Grounded Generation

**Model:** `llama-3.3-70b-versatile` via Groq.

**Exact system prompt** (from `src/generate.py`):

```
You are a helpful assistant answering questions about CS internships and early career advice.
Answer the user's question using ONLY the information provided in the context below.
Do not use any knowledge from your training data.
If the provided context does not contain enough information to answer the question, respond with exactly:
"I don't have enough information in my documents to answer that question."
Always cite your sources at the end of your response using the format:
Sources: [post title] (r/subreddit)
```

**How source attribution is programmatically guaranteed:**

1. Retrieved chunks are formatted with post title and subreddit in the context block: `[Document N — {title} from r/{subreddit}]`.
2. After generation, `build_sources_line()` deduplicates chunks by `(post_title, subreddit)` and builds a `Sources:` line from chunk metadata.
3. If the LLM omits citations, the sources line is appended to the answer automatically (`if "Sources:" not in answer: answer = f"{answer}\n\n{sources}"`).
4. If the LLM returns the fallback refusal string, the answer is replaced with the exact fallback — no training-data hallucination.

---

## Example Responses

### Example 1 — Q1 (social skills vs technical skills)

**Query:** What do students say about social skills vs technical skills in tech jobs?

**Answer:**

> Students and professionals in the tech industry suggest that social skills and being likeable are more important than technical skills for career advancement. Many commenters agree that having good social skills and being able to work well with others is more valuable than being an exceptional coder, as social skills can secure positions and build trust with colleagues. One commenter notes that "social skills/personality >>> tech skills" and that it's easier to improve technical skills than to fix personality issues.
>
> Sources: 4 years at Big tech. Being likeable beats being productive every single time (r/cscareerquestions)

**Sources field:** `Sources: [4 years at Big tech. Being likeable beats being productive every single time] (r/cscareerquestions)`

### Example 2 — Q3 (application volume)

**Query:** How many job applications did students send before getting an offer?

**Answer:**

> The student sent over 2000 job applications before getting an offer.
>
> Sources: My job search (r/csMajors)

**Sources field:** `Sources: [My job search] (r/csMajors)`

### Example 3 — Out-of-scope refusal

**Query:** What is the best programming language for machine learning?

**Answer:**

> I don't have enough information in my documents to answer that question.

**Sources field:** `Sources: [4 years at Big tech. Being likeable beats being productive every single time] (r/cscareerquestions), [How is your team reviewing all the AI generated code?] (r/SoftwareEngineering), [Can't stop tearing up, got my first FAANG offer from Apple] (r/csMajors), [[Breaking] AWS Cloud Chief says "replacing junior employees with AI is one of the dumbest things I've ever heard". The tide is shifting back.] (r/cscareerquestions)`

_(Sources are still listed from retrieved chunks, but the answer body is the exact refusal string — no ML language recommendation was generated.)_

---

## Query Interface

Entry point: `uv run python app.py` → `http://localhost:7860`

**Inputs:**
| Field | Type | Description |
|-------|------|-------------|
| Your question | Textbox | Plain-language query |
| Filter by subreddit | CheckboxGroup | Optional filter: cscareerquestions, csMajors, leetcode, internships, softwareengineering |
| Minimum post score | Slider (0–1000, step 50) | Filter out low-upvote posts |
| Chunking strategy | Radio | `fixed` or `paragraph` (default: fixed) |
| Use hybrid search | Checkbox | BM25 + semantic via RRF (default: on) |

**Outputs:**
| Field | Description |
|-------|-------------|
| Answer | Grounded response with citations |
| Sources | Programmatic source list from chunk metadata |
| Retrieved chunks (debug) | Top-k chunks with RRF scores and previews |

Conversational memory is maintained via `gr.State` (last 3 turns). Retrieval uses only the current query, not history.

### Sample Interaction Transcript

**Query:** What do students say about social skills vs technical skills in tech jobs?

**Answer:**

> Students and professionals in the tech industry suggest that social skills and being likeable are more important than technical skills for career advancement. Many comments mention that having good social skills can secure a position, build trust, and lead to better work relationships, even if one's technical skills are not exceptional. It's stated that hard skills are learnable, but soft skills are more valuable and harder to develop.
>
> Sources: 4 years at Big tech. Being likeable beats being productive every single time (r/cscareerquestions)

**Sources:** `Sources: [4 years at Big tech. Being likeable beats being productive every single time] (r/cscareerquestions)`

---

## Evaluation Report

| # | Question | Expected answer | System response (summarized) | Retrieval quality | Response accuracy |
|---|----------|-----------------|------------------------------|-------------------|-------------------|
| 1 | Social skills vs technical skills | Likeability more important than raw productivity at big tech | Social skills and being likeable matter more than technical skills for career advancement | Relevant | Accurate |
| 2 | Meta interview experience | Hundreds of LeetCode problems, long grind, relationship difficulties | 350 LC problems, Blind/subreddit research, YouTube mocks (fixed); 6-month daily grind (paragraph) | Partially relevant (fixed) | Partially accurate (fixed) / Accurate (paragraph) |
| 3 | Job application volume | Hundreds to 2000+ applications | Over 2000 applications before offer (r/csMajors "My job search") | Relevant | Accurate |
| 4 | Return offer after internship | Erroneous offer then rescinded | Mistaken return offer post; commenters discuss the error | Relevant | Partially accurate |
| 5 | AI code review | Teams struggling; stricter review, skepticism | Review volume unsustainable with AI-generated PRs; pushback on AI usage | Relevant | Accurate |

### Detailed Results by Chunking Strategy

| # | Question | Expected Answer | System Response (fixed) | Accuracy (fixed) | System Response (paragraph) | Accuracy (paragraph) |
|---|----------|-----------------|-------------------------|------------------|----------------------------|---------------------|
| 1 | Social skills vs technical skills in tech jobs | Social skills and likeability cited as more important than raw productivity at big tech | Social skills and being likeable matter more than technical skills; commenters note social skills secured big tech positions | Accurate | Same core theme — likeability and communication valued over cutting-edge technical skill | Accurate |
| 2 | Meta software engineering interview experience | Hundreds of LeetCode problems, behavioral prep, multiple rounds, long grind, relationship difficulties | Cites 350 LeetCode questions, scouring subreddits/Blind, watching mock system design on YouTube. Does not mention breakup narrative | Partially accurate | 6 months of daily prep, 5+ LeetCode questions/day, subreddit/Blind research, mock system design — led to Meta offer | Accurate |
| 3 | Job application volume before offer | Hundreds to 2000+ applications; volume and persistence themes | "Over 2000 job applications" before getting an offer (r/csMajors "My job search") | Accurate | "Roughly 2k applications" before offer (r/csMajors "My job search") | Accurate |
| 4 | Return offer after summer internship | Unexpected channels; erroneous offer then rescinded | Mentions mistaken return offer post and commenters wanting the offer upheld after the error. Thin on rescinded detail | Partially accurate | Notes mistaken return offer context; acknowledges limited general discussion beyond the error case | Partially accurate |
| 5 | AI-generated code review | Teams struggling; stricter review, pair review, skepticism | Teams struggling with review volume from AI-generated code; 30–60 min/day unsustainable; AI as additional filter, not sole filter | Accurate | Teams making PRs faster than they can be reviewed; pushback on AI usage; review burden increasing | Accurate |

**Overall:** 4/5 accurate (best strategy per question), 1/5 partially accurate (Q4). Paragraph strategy: 4/5 accurate. Fixed strategy: 3/5 accurate.

Full details in [eval/evaluation_report.md](eval/evaluation_report.md).

---

## Failure Case Analysis

**Question:** Q2 — Meta software engineering interview experience

**What retrieval returned (fixed strategy):** Apple FAANG offer post ranked 1st, likeability post 2nd, Meta post 3rd.

**Root cause:** The Meta post ranked 3rd rather than 1st because the post title emphasizes the emotional narrative (breakup) rather than the technical content (interview prep). The embedding model scored the Apple FAANG post higher due to stronger interview-experience signals in its title and body. This is a chunk metadata problem — the post title, which is embedded as part of the chunk context, does not reflect the post's primary technical content.

**Impact on generation (fixed):** Despite poor retrieval ranking, the Meta post was still included in the top-5 context window, so the answer partially captured LeetCode grind details (350 problems, Blind, YouTube mocks) but missed the relationship/breakup narrative.

**What I would change:** Store a content-summary field in chunk metadata separate from the Reddit title, or filter by subreddit (r/leetcode) for company-specific interview queries.

---

## Spec Reflection

**One way PLANNING.md guided implementation:** The exact processed document format (SUBREDDIT, POST_ID, POST_TITLE headers) made it straightforward to attach metadata to every chunk without custom parsing per pipeline stage. The grounding prompt specification and exact fallback string gave a clear, testable contract for generation — I could verify out-of-scope queries returned the refusal verbatim.

**One way implementation diverged from the spec:** The original evaluation questions in PLANNING.md (internship with no experience, LeetCode count, GPA, behavioral prep, return offer difficulty) were written before scraping and did not match the actual document content. After collecting real Reddit posts — which skewed toward job search grind, likeability at big tech, FAANG offer stories, and AI code review — the evaluation questions were rewritten to align with what the corpus actually contains. The pipeline architecture and chunking strategies followed the spec unchanged.

---

## AI Usage

**Instance 1 — Pipeline implementation**

- *What I gave the AI:* AGENTS.md and PLANNING.md specs describing the full RAG pipeline (scraper, ingest, chunking, embed, retrieval, generate, Gradio app).
- *What it produced:* Complete implementation of all six `src/` modules and `app.py`, plus initial evaluation scaffolding.
- *What I changed or overrode:* Moved subreddit listing JSON files to `data/raw/listings/` after ingest crashed on non-post-format files. Rewrote evaluation questions after real data was collected. Fixed RRF merge logic and BM25 filter syntax in `retrieval.py` during testing.

**Instance 2 — Evaluation and README completion**

- *What I gave the AI:* Instructions to run the full pipeline against 10 real Reddit documents, complete `eval/evaluation_report.md`, and fill README.md from actual repo outputs.
- *What it produced:* End-to-end pipeline run (233 fixed / 416 paragraph chunks), full 5-question evaluation with accuracy judgments, Gradio UI tests via Playwright in distrobox, and this README.
- *What I changed or overrode:* Verified all chunk text and responses against `data/processed/`, `eval/full_eval_results.json`, and `eval/ui_playwright_results.json` rather than accepting AI-generated summaries. Documented Q2 retrieval failure with the specific metadata/title mismatch root cause.

---

## Running the Pipeline

```bash
uv pip install -r requirements.txt

# Step 1: scrape (one-time)
uv run python src/scraper.py

# Step 2: clean and format
uv run python src/ingest.py

# Step 3: chunk, embed, load ChromaDB
uv run python src/embed.py

# Step 4: test retrieval
uv run python src/retrieval.py --test

# Step 5: launch Gradio UI
uv run python app.py
```

Set `GROQ_API_KEY` in `.env` for generation.
