"""Supabase client configuration and database helpers."""
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import HTTPException
from supabase import create_client

load_dotenv(Path(__file__).resolve().parent / ".env", override=True)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SECRET_KEY = os.getenv("SUPABASE_SECRET_KEY")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY") or os.getenv("VITE_SUPABASE_ANON_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_SECRET_KEY) if SUPABASE_URL and SUPABASE_SECRET_KEY else None


def get_database():
    if supabase is None:
        raise HTTPException(status_code=503, detail="Database is not configured.")
    return supabase


def execute_query(query_builder: Any) -> Any:
    try:
        return query_builder.execute()
    except Exception as exc:
        print("Supabase query failed:", type(exc).__name__)
        raise HTTPException(status_code=502, detail="Database request failed.") from exc
