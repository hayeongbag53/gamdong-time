import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def _default_sqlite_uri():
    # Vercel's serverless filesystem is read-only outside /tmp, and /tmp is
    # not persistent across invocations/cold starts, so this is only a demo
    # database there — set DATABASE_URL (e.g. Supabase Postgres) for real
    # persistence in production.
    if os.environ.get("VERCEL"):
        return "sqlite:////tmp/custom_shop.db"
    return f"sqlite:///{BASE_DIR / 'custom_shop.db'}"


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-secret-change-me")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") or _default_sqlite_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = BASE_DIR / "static" / "uploads" / "products"

    # AI provider is pluggable: set AI_PROVIDER=anthropic and ANTHROPIC_API_KEY
    # to enable real LLM-backed recommendations. Without a key, the app falls
    # back to a deterministic rule-based generator so the whole flow still
    # works out of the box.
    AI_PROVIDER = os.environ.get("AI_PROVIDER", "rule_based")
    ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
    ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-5")
