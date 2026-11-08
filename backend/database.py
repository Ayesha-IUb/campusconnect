"""Supabase client configuration and shared database helpers."""

import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import HTTPException, status
from supabase import create_client

# Load backend/.env for local development. Hosting variables take precedence only
# when they are not overridden by this local file, matching the existing setup.
load_dotenv(Path(__file__).resolve().parent / ".env", override=True)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SECRET_KEY = os.getenv("SUPABASE_SECRET_KEY")

# The privileged client must remain on the backend. Never expose this key to Vite.
supabase = None
if SUPABASE_URL and SUPABASE_SECRET_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_SECRET_KEY)


def get_database():
    """Return the configured Supabase client or a clear service error."""
    if supabase is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is not configured.",
        )
    return supabase


def execute_query(query_builder: Any) -> Any:
    """Run a Supabase query and return a safe API error on failure."""
    try:
        return query_builder.execute()
    except Exception as exc:
        print("Supabase query failed:", type(exc).__name__)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Database request failed.",
        ) from exc
