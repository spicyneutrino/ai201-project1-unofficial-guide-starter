"""Convert raw Reddit JSON into cleaned plain-text documents."""

import html
import json
import re
from datetime import datetime, timezone
from pathlib import Path

RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"
PROCESSED_DIR = Path(__file__).resolve().parent.parent / "data" / "processed"


def clean_text(text: str) -> str:
    if not text:
        return ""
    text = html.unescape(text)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def format_date(created_utc: float) -> str:
    return datetime.fromtimestamp(created_utc, tz=timezone.utc).strftime("%Y-%m-%d")


def flatten_comments(children: list, depth: int = 0) -> list[dict]:
    comments: list[dict] = []
    for child in children:
        if child.get("kind") != "t1":
            continue
        data = child.get("data", {})
        body = data.get("body", "")
        score = data.get("score", 0)

        if body in ("[deleted]", "[removed]") or score < 3 or depth > 2:
            replies = data.get("replies")
            if isinstance(replies, dict):
                reply_children = replies.get("data", {}).get("children", [])
                comments.extend(flatten_comments(reply_children, depth + 1))
            continue

        comments.append({"body": clean_text(body), "score": score})

        replies = data.get("replies")
        if isinstance(replies, dict):
            reply_children = replies.get("data", {}).get("children", [])
            comments.extend(flatten_comments(reply_children, depth + 1))

    return comments


def parse_raw_json(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    post = data[0]["data"]["children"][0]["data"]
    comment_children = data[1]["data"]["children"]
    comments = flatten_comments(comment_children)
    comments.sort(key=lambda c: c["score"], reverse=True)

    subreddit = post["subreddit"]
    post_id = post["id"]
    return {
        "subreddit": subreddit,
        "post_id": post_id,
        "post_title": clean_text(post.get("title", "")),
        "post_score": post.get("score", 0),
        "post_url": f"https://www.reddit.com/r/{subreddit}/comments/{post_id}/",
        "post_date": format_date(post.get("created_utc", 0)),
        "post_body": clean_text(post.get("selftext", "")),
        "comments": comments,
    }


def build_document(parsed: dict) -> str:
    lines = [
        f"SUBREDDIT: {parsed['subreddit']}",
        f"POST_ID: {parsed['post_id']}",
        f"POST_TITLE: {parsed['post_title']}",
        f"POST_SCORE: {parsed['post_score']}",
        f"POST_URL: {parsed['post_url']}",
        f"POST_DATE: {parsed['post_date']}",
        "",
        "POST:",
        parsed["post_body"],
        "",
        "COMMENTS:",
    ]
    for comment in parsed["comments"]:
        lines.append(f"[score: {comment['score']}] {comment['body']}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def process_file(raw_path: Path) -> Path:
    parsed = parse_raw_json(raw_path)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    out_path = PROCESSED_DIR / f"{parsed['subreddit']}_{parsed['post_id']}.txt"
    out_path.write_text(build_document(parsed), encoding="utf-8")
    return out_path


def main() -> None:
    raw_files = sorted(RAW_DIR.glob("*.json"))
    if not raw_files:
        print("No raw JSON files found in data/raw/")
        return
    for raw_path in raw_files:
        out = process_file(raw_path)
        print(f"Processed {raw_path.name} -> {out.name}")
    print(f"Done. {len(raw_files)} documents written.")


if __name__ == "__main__":
    main()
