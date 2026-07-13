"""SAGE API application entrypoint."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import settings

app = FastAPI(
    title=settings.app_name,
    description=(
        f"{settings.app_description} — a governed decision operating system for "
        "funding evidence, strategic alignment, sustainability and measurable outcomes."
    ),
    version="0.2.0",
)

# CORS for the local React dev server. Tighten for production (PRD 13).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/health", tags=["Meta"])
def health() -> dict:
    return {"status": "ok", "app": settings.app_name, "environment": settings.environment}
