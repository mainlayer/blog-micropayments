"""
Blog Micropayments API

Each blog post costs $0.01 to read in full.
Free preview shows the first 200 characters.
"""

from __future__ import annotations

import os
from datetime import datetime

from fastapi import FastAPI, HTTPException, Header
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi import Request
from mainlayer import MainlayerClient

from .models import Post, PostSummary, PostsListResponse, PaymentRequiredResponse

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Blog Micropayments API",
    description="A blog where each post costs $0.01 — pay per read with Mainlayer.",
    version="1.0.0",
)

templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "..", "templates"))

ml = MainlayerClient(api_key=os.environ.get("MAINLAYER_API_KEY", ""))
RESOURCE_ID = os.environ.get("MAINLAYER_RESOURCE_ID", "")

# ---------------------------------------------------------------------------
# In-memory post database (replace with real DB in production)
# ---------------------------------------------------------------------------

_POSTS: list[dict] = [
    {
        "id": 1,
        "title": "How AI Agents Are Changing the Economy",
        "author": "Alice Nguyen",
        "published_at": "2025-03-01T09:00:00Z",
        "tags": ["AI", "economics", "agents"],
        "content": (
            "Artificial intelligence agents are rapidly becoming economic actors in their own right. "
            "Unlike traditional software, AI agents can autonomously negotiate, purchase, and transact "
            "on behalf of their principals — or entirely on their own. This shift is creating new "
            "markets that were previously unimaginable.\n\n"
            "Consider the data economy: an AI agent tasked with market research can now query paid "
            "data APIs, retrieve the results, synthesise insights, and bill the cost back to its "
            "operator — all without human intervention. The friction of micro-transactions has "
            "historically prevented this kind of fine-grained commerce, but payment infrastructure "
            "purpose-built for agents is removing that barrier.\n\n"
            "Early adopters are seeing 10–40% reductions in research costs as agents replace manual "
            "data gathering. The implications for knowledge work are profound."
        ),
        "read_time_minutes": 4,
    },
    {
        "id": 2,
        "title": "The Architecture of Agent-Native APIs",
        "author": "Bob Okafor",
        "published_at": "2025-03-10T11:30:00Z",
        "tags": ["API design", "agents", "architecture"],
        "content": (
            "Building APIs for AI agents requires rethinking several assumptions baked into "
            "traditional REST design. Human users tolerate latency and error messages; agents "
            "require deterministic schemas, machine-readable error codes, and per-request "
            "payment semantics.\n\n"
            "HTTP 402 Payment Required — long dormant — is now seeing its intended use. An "
            "agent that encounters a 402 can parse a structured payment payload, authorise "
            "the spend within its budget policy, retry the request with a valid payment token, "
            "and continue the workflow without surfacing anything to a human operator.\n\n"
            "Key design principles: idempotent endpoints, structured error envelopes, "
            "cost metadata in response headers, and webhook callbacks for async billing events."
        ),
        "read_time_minutes": 5,
    },
    {
        "id": 3,
        "title": "Micro-transactions at Scale: Lessons from the Field",
        "author": "Clara Benson",
        "published_at": "2025-03-18T14:00:00Z",
        "tags": ["payments", "scale", "engineering"],
        "content": (
            "When you process millions of sub-cent transactions per day, the engineering "
            "challenges shift from payment logic to reliability and observability. A failed "
            "$0.001 transaction is economically trivial; a 0.1% failure rate across 10 million "
            "daily transactions is not.\n\n"
            "The first lesson: idempotency keys are non-negotiable. Every agent request should "
            "carry a deterministic idempotency key so that network retries do not result in "
            "double charges. The second lesson: async settlement beats synchronous blocking. "
            "Validate the payment token upfront, serve the content, settle in the background.\n\n"
            "Circuit breakers, dead-letter queues, and per-agent spend caps round out a "
            "production-grade micropayment system."
        ),
        "read_time_minutes": 6,
    },
    {
        "id": 4,
        "title": "Why Open Data Is Not Free Data",
        "author": "Alice Nguyen",
        "published_at": "2025-03-25T10:00:00Z",
        "tags": ["data", "open source", "monetization"],
        "content": (
            "The open data movement assumed that removing access barriers would maximise value. "
            "It succeeded on that axis — and created an unexpected problem: without revenue, "
            "data publishers cannot sustain the infrastructure required to keep datasets fresh, "
            "accurate, and reliable.\n\n"
            "Micropayment models offer a middle path. Data remains accessible to anyone with a "
            "token; the cost per query is low enough that it does not deter legitimate use but "
            "high enough to fund operations. AI agents, which issue orders of magnitude more "
            "queries than humans, become net contributors to the data ecosystem rather than "
            "free riders.\n\n"
            "The result is a sustainable open data commons — not charity, but a functional market."
        ),
        "read_time_minutes": 4,
    },
    {
        "id": 5,
        "title": "Getting Started with Agent Payments in Python",
        "author": "Dan Park",
        "published_at": "2025-04-01T08:00:00Z",
        "tags": ["tutorial", "Python", "agents", "payments"],
        "content": (
            "In this tutorial we walk through integrating Mainlayer payment tokens into a "
            "Python AI agent built with the `httpx` library.\n\n"
            "Step 1: Install the SDK.\n"
            "```bash\npip install mainlayer httpx\n```\n\n"
            "Step 2: Acquire a token for the resource you want to access.\n"
            "```python\nimport mainlayer\nclient = mainlayer.MainlayerClient(api_key='YOUR_KEY')\n"
            "token = client.tokens.create(resource_id='RESOURCE_ID')\n```\n\n"
            "Step 3: Attach the token to your HTTP request.\n"
            "```python\nimport httpx\nresp = httpx.get(\n"
            "    'https://api.example.com/data',\n"
            "    headers={'X-Mainlayer-Token': token.value}\n)\n```\n\n"
            "That's it. The API verifies the token server-side; you receive the data."
        ),
        "read_time_minutes": 7,
    },
]


def _make_summary(raw: dict) -> PostSummary:
    return PostSummary(
        id=raw["id"],
        title=raw["title"],
        author=raw["author"],
        published_at=raw["published_at"],
        tags=raw["tags"],
        preview=raw["content"][:200],
        read_time_minutes=raw["read_time_minutes"],
    )


def _make_post(raw: dict, include_content: bool = False) -> Post:
    return Post(
        id=raw["id"],
        title=raw["title"],
        author=raw["author"],
        published_at=raw["published_at"],
        tags=raw["tags"],
        preview=raw["content"][:200],
        content=raw["content"] if include_content else None,
        read_time_minutes=raw["read_time_minutes"],
    )


# ---------------------------------------------------------------------------
# Payment dependency
# ---------------------------------------------------------------------------

async def require_payment(x_mainlayer_token: str = Header(...)):
    """Verify Mainlayer payment token; raise 402 if not authorised."""
    access = await ml.resources.verify_access(RESOURCE_ID, x_mainlayer_token)
    if not access.authorized:
        raise HTTPException(
            status_code=402,
            detail={
                "error": "payment_required",
                "message": "This post costs $0.01 to read. Get a token at mainlayer.fr",
                "cost_usd": 0.01,
                "payment_url": "https://mainlayer.fr",
            },
        )
    return access


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    posts = [_make_summary(p) for p in _POSTS]
    return templates.TemplateResponse("index.html", {"request": request, "posts": posts})


@app.get("/posts", response_model=PostsListResponse)
async def list_posts():
    """List all posts with free previews (first 200 chars)."""
    return PostsListResponse(
        posts=[_make_summary(p) for p in _POSTS],
        total=len(_POSTS),
    )


@app.get(
    "/posts/{post_id}",
    response_model=Post,
    responses={
        402: {"model": PaymentRequiredResponse, "description": "Payment required"},
        404: {"description": "Post not found"},
    },
)
async def get_post(post_id: int, x_mainlayer_token: str = Header(...)):
    """Retrieve full post content. Requires a valid Mainlayer payment token."""
    raw = next((p for p in _POSTS if p["id"] == post_id), None)
    if raw is None:
        raise HTTPException(status_code=404, detail="Post not found")

    access = await ml.resources.verify_access(RESOURCE_ID, x_mainlayer_token)
    if not access.authorized:
        raise HTTPException(
            status_code=402,
            detail={
                "error": "payment_required",
                "message": "This post costs $0.01 to read. Get a token at mainlayer.fr",
                "cost_usd": 0.01,
                "payment_url": "https://mainlayer.fr",
            },
        )

    return _make_post(raw, include_content=True)


@app.get("/health")
async def health():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}
