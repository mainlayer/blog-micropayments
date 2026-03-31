"""Pydantic models for the Blog Micropayments API."""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


class Post(BaseModel):
    id: int
    title: str
    author: str
    published_at: str
    tags: list[str]
    preview: str = Field(description="First 200 characters of content")
    content: Optional[str] = Field(None, description="Full content — requires payment")
    read_time_minutes: int


class PostSummary(BaseModel):
    id: int
    title: str
    author: str
    published_at: str
    tags: list[str]
    preview: str
    read_time_minutes: int
    cost_usd: float = 0.01


class PostsListResponse(BaseModel):
    posts: list[PostSummary]
    total: int
    note: str = "Each post costs $0.01 to read in full. Pass X-Mainlayer-Token header."


class PaymentRequiredResponse(BaseModel):
    error: str = "payment_required"
    message: str = "This post requires payment. Get a token at mainlayer.fr"
    cost_usd: float = 0.01
    payment_url: str = "https://mainlayer.fr"
