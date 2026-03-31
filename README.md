# blog-micropayments
![CI](https://github.com/mainlayer/blog-micropayments/actions/workflows/ci.yml/badge.svg)

A blog where every post costs $0.01 to read — humans and AI agents pay via Mainlayer. Free previews (first 200 chars) are available without authentication.

## Install

```bash
pip install mainlayer httpx
```

## Quickstart

```python
import httpx

# List posts (free)
posts = httpx.get("https://your-blog.com/posts").json()
print(posts)

# Read a full post (requires token)
response = httpx.get(
    "https://your-blog.com/posts/1",
    headers={"X-Mainlayer-Token": "your-token"}
)
print(response.json()["content"])
```

## Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/posts` | None | List all posts with free previews |
| `GET` | `/posts/{id}` | Token | Read full post content ($0.01) |
| `GET` | `/` | None | HTML blog index |
| `GET` | `/health` | None | Health check |

## Running locally

```bash
pip install -e ".[dev]"
uvicorn src.main:app --reload
```

## Running tests

```bash
pytest tests/
```

## Environment variables

| Variable | Description |
|----------|-------------|
| `MAINLAYER_API_KEY` | Your Mainlayer API key |
| `MAINLAYER_RESOURCE_ID` | The resource ID for this blog |

📚 [mainlayer.fr](https://mainlayer.fr)
