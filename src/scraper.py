"""Fetch top Reddit posts and save raw JSON to data/raw/."""

import json
import time
from pathlib import Path

import requests

HEADERS = {"User-Agent": "unofficial-guide-rag/1.0"}
SUBREDDITS = [
    "cscareerquestions",
    "csMajors",
    "leetcode",
    "internships",
    "softwareengineering",
]
TARGET_PER_SUB = 3
RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"


def fetch_json(url: str) -> dict | list:
    response = requests.get(url, headers=HEADERS, timeout=30)
    time.sleep(1)
    response.raise_for_status()
    return response.json()


def is_valid_post(post_data: dict) -> bool:
    if post_data.get("stickied"):
        return False
    if post_data.get("score", 0) < 50:
        return False
    author = (post_data.get("author") or "").lower()
    if author in {"automoderator", "moderator"}:
        return False
    return True


def raw_path(subreddit: str, post_id: str) -> Path:
    return RAW_DIR / f"{subreddit}_{post_id}.json"


def save_raw(subreddit: str, post_id: str, data: list) -> Path:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    path = raw_path(subreddit, post_id)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return path


def scrape_subreddit(name: str) -> list[str]:
    listing_url = f"https://www.reddit.com/r/{name}/top.json?t=year&limit=10"
    listing = fetch_json(listing_url)
    saved_ids: list[str] = []

    for child in listing["data"]["children"]:
        if len(saved_ids) >= TARGET_PER_SUB:
            break

        post_data = child["data"]
        post_id = post_data["id"]

        if raw_path(name, post_id).exists():
            print(f"  skip existing {name}_{post_id}")
            saved_ids.append(post_id)
            continue

        if not is_valid_post(post_data):
            continue

        post_url = (
            f"https://www.reddit.com/r/{name}/comments/{post_id}.json"
            f"?sort=top&limit=100"
        )
        post_json = fetch_json(post_url)
        save_raw(name, post_id, post_json)
        saved_ids.append(post_id)
        print(f"  saved {name}_{post_id} (score={post_data.get('score')})")

    return saved_ids


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    total = 0
    for subreddit in SUBREDDITS:
        print(f"Scraping r/{subreddit}...")
        ids = scrape_subreddit(subreddit)
        print(f"  {len(ids)} posts for r/{subreddit}")
        total += len(ids)
    print(f"Done. {total} posts across {len(SUBREDDITS)} subreddits.")


if __name__ == "__main__":
    main()
