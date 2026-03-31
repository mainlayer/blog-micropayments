"""
Example: AI agent fetching a paid blog post via the Mainlayer token.

Usage:
    MAINLAYER_API_KEY=your_key python examples/fetch_post.py
"""

import os
import httpx

BASE_URL = os.environ.get("BLOG_API_URL", "http://localhost:8000")
TOKEN = os.environ.get("MAINLAYER_TOKEN", "your-mainlayer-token-here")


def list_posts() -> list[dict]:
    resp = httpx.get(f"{BASE_URL}/posts")
    resp.raise_for_status()
    data = resp.json()
    print(f"Found {data['total']} posts:")
    for post in data["posts"]:
        print(f"  [{post['id']}] {post['title']} — preview: {post['preview'][:80]}…")
    return data["posts"]


def fetch_full_post(post_id: int, token: str) -> dict:
    resp = httpx.get(
        f"{BASE_URL}/posts/{post_id}",
        headers={"X-Mainlayer-Token": token},
    )
    if resp.status_code == 402:
        detail = resp.json()["detail"]
        print(f"Payment required: {detail['message']}")
        print(f"Get a token at: {detail['payment_url']}")
        return {}
    resp.raise_for_status()
    post = resp.json()
    print(f"\n--- {post['title']} ---")
    print(f"By {post['author']} on {post['published_at'][:10]}")
    print()
    print(post["content"])
    return post


if __name__ == "__main__":
    posts = list_posts()
    if posts:
        fetch_full_post(posts[0]["id"], TOKEN)
