"""
Supabase Database Client
Handles all database operations with connection pooling and error handling.
"""

import os
import streamlit as st
from supabase import create_client, Client
from dotenv import load_dotenv
from typing import Optional, Dict, Any, List
import logging

load_dotenv()
logger = logging.getLogger(__name__)


@st.cache_resource
def _get_cached_anon_client() -> Client:
    url = os.getenv("SUPABASE_URL", "")
    key = os.getenv("SUPABASE_ANON_KEY", "")
    if not url or not key:
        raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY must be set in .env")
    return create_client(url, key)


@st.cache_resource
def _get_cached_admin_client() -> Client:
    url = os.getenv("SUPABASE_URL", "")
    key = os.getenv("SUPABASE_SERVICE_KEY", "")
    if not url or not key:
        raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in .env")
    return create_client(url, key)


def get_supabase_client() -> Client:
    """Return a Supabase client dynamically based on the logged-in user session."""
    user = st.session_state.get("user") if "user" in st.session_state else None
    user_email = user.get("email", "") if user else ""
    is_admin_user = user_email.strip().lower() == "admin@gmail.com" or user_email.startswith("admin@")
    
    if is_admin_user:
        if "supabase_admin_client" not in st.session_state:
            url = os.getenv("SUPABASE_URL", "")
            key = os.getenv("SUPABASE_SERVICE_KEY", "")
            if not url or not key:
                raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in .env")
            st.session_state["supabase_admin_client"] = create_client(url, key)
        return st.session_state["supabase_admin_client"]
    else:
        if "supabase_anon_client" not in st.session_state:
            url = os.getenv("SUPABASE_URL", "")
            key = os.getenv("SUPABASE_ANON_KEY", "")
            if not url or not key:
                raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY must be set in .env")
            client = create_client(url, key)
            st.session_state["supabase_anon_client"] = client
            
            # Auto-restore session on this fresh client instance if token is in session_state
            if user and "access_token" in user and "refresh_token" in user:
                try:
                    client.auth.set_session(user["access_token"], user["refresh_token"])
                except Exception as e:
                    logger.error(f"Failed to auto-restore session on fresh client: {e}")
                    
        return st.session_state["supabase_anon_client"]


def get_supabase_admin() -> Client:
    """Return a cached admin Supabase client (service role — server-side only)."""
    return _get_cached_admin_client()


# ─────────────────────────────────────────────
# Generic CRUD helpers
# ─────────────────────────────────────────────

def db_insert(table: str, data: Dict[str, Any]) -> Optional[Dict]:
    try:
        client = get_supabase_client()
        res = client.table(table).insert(data).execute()
        return res.data[0] if res.data else None
    except Exception as e:
        logger.error(f"db_insert({table}) error: {e}")
        return None


def db_select(
    table: str,
    filters: Optional[Dict[str, Any]] = None,
    columns: str = "*",
    order: Optional[str] = None,
    limit: Optional[int] = None,
) -> List[Dict]:
    try:
        client = get_supabase_client()
        q = client.table(table).select(columns)
        if filters:
            for col, val in filters.items():
                q = q.eq(col, val)
        if order:
            if "." in order:
                col, direction = order.split(".", 1)
                is_desc = (direction.lower() == "desc")
                q = q.order(col, desc=is_desc)
            else:
                q = q.order(order)
        if limit:
            q = q.limit(limit)
        res = q.execute()
        return res.data or []
    except Exception as e:
        logger.error(f"db_select({table}) error: {e}")
        return []


def db_update(
    table: str,
    filters: Dict[str, Any],
    data: Dict[str, Any],
) -> Optional[Dict]:
    try:
        client = get_supabase_client()
        q = client.table(table).update(data)
        for col, val in filters.items():
            q = q.eq(col, val)
        res = q.execute()
        return res.data[0] if res.data else None
    except Exception as e:
        logger.error(f"db_update({table}) error: {e}")
        return None


def db_upsert(table: str, data: Dict[str, Any]) -> Optional[Dict]:
    try:
        client = get_supabase_client()
        res = client.table(table).upsert(data).execute()
        return res.data[0] if res.data else None
    except Exception as e:
        logger.error(f"db_upsert({table}) error: {e}")
        return None


def db_delete(table: str, filters: Dict[str, Any]) -> bool:
    try:
        client = get_supabase_client()
        q = client.table(table).delete()
        for col, val in filters.items():
            q = q.eq(col, val)
        q.execute()
        return True
    except Exception as e:
        logger.error(f"db_delete({table}) error: {e}")
        return False


# ─────────────────────────────────────────────
# Domain-specific helpers
# ─────────────────────────────────────────────

def get_profile(user_id: str) -> Optional[Dict]:
    rows = db_select("profiles", {"id": user_id})
    return rows[0] if rows else None


def upsert_performance(user_id: str, scores: Dict[str, float]) -> None:
    from datetime import date
    data = {"user_id": user_id, "metric_date": str(date.today()), **scores}
    db_upsert("performance_metrics", data)


def get_performance_history(user_id: str, days: int = 30) -> List[Dict]:
    try:
        client = get_supabase_client()
        from datetime import date, timedelta
        since = str(date.today() - timedelta(days=days))
        res = (
            client.table("performance_metrics")
            .select("*")
            .eq("user_id", user_id)
            .gte("metric_date", since)
            .order("metric_date")
            .execute()
        )
        return res.data or []
    except Exception as e:
        logger.error(f"get_performance_history error: {e}")
        return []


def award_xp(user_id: str, xp: int) -> None:
    try:
        client = get_supabase_client()
        client.rpc("award_xp", {"p_user_id": user_id, "p_xp": xp}).execute()
    except Exception as e:
        logger.error(f"award_xp error: {e}")


def log_audit(user_id: str, action: str, resource: str = "", resource_id: str = "") -> None:
    db_insert("audit_logs", {
        "user_id": user_id,
        "action": action,
        "resource": resource,
        "resource_id": resource_id,
    })


def upload_file_to_storage(bucket: str, path: str, file_bytes: bytes, content_type: str = "application/octet-stream") -> Optional[str]:
    """Upload a file to Supabase Storage and return its public URL."""
    try:
        client = get_supabase_client()
        client.storage.from_(bucket).upload(
            path, file_bytes, {"content-type": content_type, "upsert": "true"}
        )
        url = client.storage.from_(bucket).get_public_url(path)
        return url
    except Exception as e:
        logger.error(f"upload_file_to_storage error: {e}")
        return None
