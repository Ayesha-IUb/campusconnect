"""Supabase client configuration and safe query execution."""

import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import HTTPException, status
from supabase import create_client

# Load backend/.env locally or use environment variables on Vercel.
load_dotenv(Path(__file__).resolve().parent / ".env", override=True)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SECRET_KEY = os.getenv("SUPABASE_SECRET_KEY")

# The privileged key must remain on the backend only.
supabase = None
if SUPABASE_URL and SUPABASE_SECRET_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_SECRET_KEY)


def get_database():
    if supabase is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is not configured.",
        )
    return supabase


def execute_query(query_builder: Any) -> Any:
    try:
        return query_builder.execute()
    except Exception as exc:
        # Avoid logging credentials or raw database payloads.
        print("Supabase query failed:", type(exc).__name__)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Database request failed.",
        ) from exc
