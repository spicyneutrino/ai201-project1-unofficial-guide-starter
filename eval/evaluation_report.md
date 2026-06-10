# Evaluation Report

Evaluated on 2026-06-10 against 10 real Reddit documents across 5 subreddits (233 fixed chunks, 416 paragraph chunks). Hybrid retrieval (BM25 + semantic, RRF k=60). Generation via Groq `llama-3.3-70b-versatile`.

## Full Evaluation Table

| # | Question | Expected Answer | System Response (fixed) | Accuracy (fixed) | System Response (paragraph) | Accuracy (paragraph) |
|---|----------|-----------------|-------------------------|------------------|----------------------------|---------------------|
| 1 | Social skills vs technical skills in tech jobs | Social skills and likeability cited as more important than raw productivity at big tech | Students/professionals say social skills and being likeable matter more than technical skills for getting and keeping jobs; commenters note social skills secured big tech positions and soft skills are harder to develop than hard skills | **Accurate** | Same core theme — likeability and communication valued over cutting-edge technical skill; cites social skills securing big tech roles | **Accurate** |
| 2 | Meta software engineering interview experience | Hundreds of LeetCode problems, behavioral prep, multiple rounds, long grind, relationship difficulties | Cites 350 LeetCode questions, scouring subreddits/Blind, watching mock system design on YouTube (from Meta post in context). Does not mention breakup/relationship narrative | **Partially accurate** | 6 months of daily prep, 5+ LeetCode questions/day, subreddit/Blind research, mock system design — led to Meta offer | **Accurate** |
| 3 | Job application volume before offer | Hundreds to 2000+ applications; volume and persistence themes | "Over 2000 job applications" before getting an offer (r/csMajors "My job search") | **Accurate** | "Roughly 2k applications" before offer (r/csMajors "My job search") | **Accurate** |
| 4 | Return offer after summer internship | Unexpected channels; erroneous offer then rescinded | Mentions mistaken return offer post and commenters wanting the offer upheld after the error. Thin on rescinded detail | **Partially accurate** | Notes mistaken return offer context; acknowledges limited general discussion beyond the error case | **Partially accurate** |
| 5 | AI-generated code review | Teams struggling; stricter review, pair review, skepticism | Teams struggling with review volume from AI-generated code; 30–60 min/day unsustainable; suggestion to use AI as additional filter, not sole filter | **Accurate** | Teams making PRs faster than they can be reviewed; pushback on AI usage; review burden increasing | **Accurate** |

---

## Retrieval Results (Top 3 Chunks per Query & Strategy)

### Q1: Social skills vs technical skills

**Fixed — top 3:**
1. r/cscareerquestions — *4 years at Big tech. Being likeable beats being productive every single time*
2. r/cscareerquestions — *4 years at Big tech. Being likeable beats being productive every single time*
3. r/cscareerquestions — *4 years at Big tech. Being likeable beats being productive every single time*

**Paragraph — top 3:**
1. r/cscareerquestions — *4 years at Big tech. Being likeable beats being productive every single time*
2. r/leetcode — *it takes time*
3. r/cscareerquestions — *4 years at Big tech. Being likeable beats being productive every single time*

---

### Q2: Meta interview experience

**Fixed — top 3:**
1. r/csMajors — *Can't stop tearing up, got my first FAANG offer from Apple*
2. r/cscareerquestions — *4 years at Big tech. Being likeable beats being productive every single time*
3. r/leetcode — *Got dumped by GF of 4 years but got a Meta offer today*

**Paragraph — top 3:**
1. r/csMajors — *Can't stop tearing up, got my first FAANG offer from Apple*
2. r/leetcode — *Got dumped by GF of 4 years but got a Meta offer today*
3. r/leetcode — *Got dumped by GF of 4 years but got a Meta offer today*

---

### Q3: Job application volume

**Fixed — top 3:**
1. r/csMajors — *My job search*
2. r/csMajors — *My job search*
3. r/csMajors — *My job search*

**Paragraph — top 3:**
1. r/csMajors — *My job search*
2. r/cscareerquestions — *4 years at Big tech. Being likeable beats being productive every single time*
3. r/csMajors — *My job search*

---

### Q4: Return offer after internship

**Fixed — top 3:**
1. r/internships — *Got sent a return offer by mistake LMAO*
2. r/csMajors — *My job search*
3. r/internships — *Got sent a return offer by mistake LMAO*

**Paragraph — top 3:**
1. r/internships — *Got sent a return offer by mistake LMAO*
2. r/internships — *Got sent a return offer by mistake LMAO*
3. r/internships — *Got caught sleeping with 2 days left on my internship.*

---

### Q5: AI code review

**Fixed — top 3:**
1. r/SoftwareEngineering — *How is your team reviewing all the AI generated code?*
2. r/SoftwareEngineering — *How is your team reviewing all the AI generated code?*
3. r/SoftwareEngineering — *How is your team reviewing all the AI generated code?*

**Paragraph — top 3:**
1. r/SoftwareEngineering — *How is your team reviewing all the AI generated code?*
2. r/SoftwareEngineering — *Our team stopped doing standups, story points and retros — and nothing broke*
3. r/SoftwareEngineering — *How is your team reviewing all the AI generated code?*

---

## Gradio UI Tests

Tested via `uv run python app.py` at `http://localhost:7860` (default: fixed strategy, hybrid search enabled).

### UI-Q1: "What do students say about social skills vs technical skills in tech jobs?"

**Answer:**
> Students and professionals in the tech industry suggest that social skills and being likeable are more important than technical skills for career advancement. Many comments mention that having good social skills can secure a position, build trust, and lead to better work relationships, even if one's technical skills are not exceptional. It's stated that hard skills are learnable, but soft skills are more valuable and harder to develop.
>
> Sources: 4 years at Big tech. Being likeable beats being productive every single time (r/cscareerquestions)

**Sources field:**
> Sources: [4 years at Big tech. Being likeable beats being productive every single time] (r/cscareerquestions)

---

### UI-Q3: "How many job applications did students send before getting an offer?"

**Answer:**
> The students sent over 2000 job applications before getting an offer.
>
> Sources: My job search (r/csMajors)

**Sources field:**
> Sources: [My job search] (r/csMajors)

---

### UI — Out-of-scope: "What is the best programming language for machine learning?"

**Answer:**
> I don't have enough information in my documents to answer that question.

**Sources field:**
> Sources: [4 years at Big tech. Being likeable beats being productive every single time] (r/cscareerquestions), [How is your team reviewing all the AI generated code?] (r/SoftwareEngineering), [Can't stop tearing up, got my first FAANG offer from Apple] (r/csMajors), [[Breaking] AWS Cloud Chief says "replacing junior employees with AI is one of the dumbest things I've ever heard". The tide is shifting back.] (r/cscareerquestions)

**Grounding check:** Refusal response returned correctly — no hallucinated ML language recommendation.

---

## Failure Case Analysis

### Q2: Meta interview experience (documented failure)

**What retrieval returned (fixed strategy):** Apple FAANG offer post ranked 1st, likeability post 2nd, Meta post 3rd.

**Root cause:** The Meta post ranked 3rd rather than 1st because the post title emphasizes the emotional narrative (breakup) rather than the technical content (interview prep). The embedding model scored the Apple FAANG post higher due to stronger interview-experience signals in its title and body. This is a chunk metadata problem — the post title, which is embedded as part of the chunk context, does not reflect the post's primary technical content.

**Impact on generation (fixed):** Despite poor retrieval ranking, the Meta post was still included in the top-5 context window, so the answer partially captured LeetCode grind details (350 problems, Blind, YouTube mocks) but missed the relationship/breakup narrative.

**What I would change:** Store a content-summary field in chunk metadata separate from the Reddit title, or filter by subreddit (r/leetcode) for company-specific interview queries.

---

## Strategy Comparison

| Strategy | Accurate | Partially Accurate | Inaccurate |
|----------|----------|-------------------|------------|
| Fixed | 3 (Q1, Q3, Q5) | 2 (Q2, Q4) | 0 |
| Paragraph | 4 (Q1, Q2, Q3, Q5) | 1 (Q4) | 0 |

**Paragraph performed better** — especially on Q2 where paragraph chunks from the Meta post ranked 2nd and 3rd (vs 3rd only for fixed), producing a more complete answer including the 6-month grind timeline.

---

## Final Summary

| Metric | Value |
|--------|-------|
| Overall accuracy (best strategy per question) | **4/5 accurate**, 1/5 partially accurate |
| Fixed strategy accuracy | **3/5 accurate**, 2/5 partially accurate |
| Paragraph strategy accuracy | **4/5 accurate**, 1/5 partially accurate |
| Better strategy | **Paragraph** (wins on Q2; tie or equivalent on others) |
| Documented failure case | **Q2 (fixed)** — Meta post ranked 3rd due to title/metadata mismatch with technical content |
| Out-of-scope grounding | **Pass** — ML language query returned exact refusal string |
