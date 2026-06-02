"""
Authentication Module — Supabase Auth
Handles signup, login, Google OAuth, password reset, session management.
"""

import os
import streamlit as st
from supabase import Client
from typing import Optional, Dict, Tuple
import logging

from src.database.supabase_client import get_supabase_client, db_insert, get_profile

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# Session helpers
# ─────────────────────────────────────────────

def is_authenticated() -> bool:
    return st.session_state.get("authenticated", False) and st.session_state.get("user") is not None


def get_current_user() -> Optional[Dict]:
    return st.session_state.get("user")


def get_current_profile() -> Optional[Dict]:
    return st.session_state.get("profile")


def _store_session(user_data: Dict, profile: Optional[Dict] = None) -> None:
    st.session_state["authenticated"] = True
    st.session_state["user"] = user_data
    st.session_state["profile"] = profile or {}


def clear_session() -> None:
    for key in ["authenticated", "user", "profile", "interview_session",
                 "chat_history", "rag_index", "current_page",
                 "supabase_anon_client", "supabase_admin_client"]:
        st.session_state.pop(key, None)


# ─────────────────────────────────────────────
# Auth operations
# ─────────────────────────────────────────────

def sign_up(
    email: str,
    password: str,
    full_name: str,
    college: str = "",
    branch: str = "",
    graduation_year: Optional[int] = None,
) -> Tuple[bool, str]:
    """Register a new user with email + password."""
    try:
        client: Client = get_supabase_client()
        res = client.auth.sign_up({
            "email": email,
            "password": password,
            "options": {
                "data": {
                    "full_name": full_name,
                    "college": college,
                    "branch": branch,
                    "graduation_year": graduation_year,
                }
            }
        })
        if res.user:
            # Profile is automatically created via the DB trigger with the passed metadata.
            return True, "Account created! Please check your email to confirm."
        return False, "Signup failed. Please try again."
    except Exception as e:
        err = str(e)
        if "already registered" in err.lower():
            return False, "Email already registered. Please log in."
        logger.error(f"sign_up error: {e}")
        return False, f"Signup error: {err}"


def sign_in(email: str, password: str, remember: bool = False) -> Tuple[bool, str]:
    """Sign in with email + password."""
    try:
        # Check special admin credentials bypass
        if email.strip().lower() == "admin@gmail.com" and password == "adminadmin":
            _store_session(
                {
                    "id": "admin-mock-uuid-000000000000",
                    "email": "admin@gmail.com",
                    "access_token": "mock-admin-token",
                    "refresh_token": "mock-admin-token",
                },
                {
                    "id": "admin-mock-uuid-000000000000",
                    "full_name": "System Administrator",
                    "email": "admin@gmail.com",
                    "role": "admin",
                    "xp_points": 999999,
                    "streak_days": 999,
                    "college": "System",
                    "branch": "Admin",
                }
            )
            return True, "Login successful!"

        client: Client = get_supabase_client()
        res = client.auth.sign_in_with_password({"email": email, "password": password})
        if res.user and res.session:
            profile = get_profile(res.user.id)
            _store_session(
                {
                    "id": res.user.id,
                    "email": res.user.email,
                    "access_token": res.session.access_token,
                    "refresh_token": res.session.refresh_token,
                },
                profile,
            )
            # Update last_active
            client.table("profiles").update({"last_active": "now()"}).eq("id", res.user.id).execute()
            return True, "Login successful!"
        return False, "Invalid credentials."
    except Exception as e:
        err = str(e)
        if "invalid" in err.lower() or "credentials" in err.lower():
            return False, "Invalid email or password."
        logger.error(f"sign_in error: {e}")
        return False, f"Login error: {err}"


def sign_out() -> None:
    """Sign out the current user."""
    try:
        client: Client = get_supabase_client()
        client.auth.sign_out()
    except Exception:
        pass
    finally:
        clear_session()


def reset_password(email: str) -> Tuple[bool, str]:
    """Send password reset email."""
    try:
        client: Client = get_supabase_client()
        redirect = os.getenv("APP_URL", "http://localhost:8501")
        client.auth.reset_password_email(email, {"redirect_to": f"{redirect}/reset"})
        return True, "Password reset email sent! Check your inbox."
    except Exception as e:
        logger.error(f"reset_password error: {e}")
        return False, f"Error sending reset email: {e}"


def get_google_oauth_url() -> Tuple[Optional[str], Optional[str]]:
    """Get Google OAuth redirect URL from Supabase along with the PKCE code verifier."""
    try:
        client: Client = get_supabase_client()
        redirect = os.getenv("APP_URL", "http://localhost:8501")
        res = client.auth.sign_in_with_oauth({
            "provider": "google",
            "options": {"redirect_to": redirect},
        })
        code_verifier = None
        try:
            storage_key = getattr(client.auth, '_storage_key', None)
            if storage_key:
                code_verifier = client.auth._storage.get_item(f"{storage_key}-code-verifier")
        except Exception as ex:
            logger.warning(f"Could not extract code_verifier: {ex}")
        
        # Append code_verifier as state parameter to ensure it is returned in callback query params
        res_url = res.url
        if res_url and code_verifier:
            if "?" in res_url:
                res_url = f"{res_url}&state={code_verifier}"
            else:
                res_url = f"{res_url}?state={code_verifier}"
        return res_url, code_verifier
    except Exception as e:
        logger.error(f"google_oauth error: {e}")
        return None, None


def restore_session_from_token(access_token: str, refresh_token: str) -> bool:
    """Restore a session from stored tokens (remember-me flow)."""
    try:
        logger.info(f"Attempting to restore session. Access token len: {len(access_token) if access_token else 0}, Refresh token len: {len(refresh_token) if refresh_token else 0}")
        client: Client = get_supabase_client()
        res = client.auth.set_session(access_token, refresh_token)
        if res.user:
            profile = get_profile(res.user.id)
            if not profile:
                logger.info(f"No profile found for user {res.user.id}. Creating default profile.")
                user_meta = res.user.user_metadata or {}
                full_name = user_meta.get("full_name") or user_meta.get("name") or "Google User"
                try:
                    from src.database.supabase_client import get_supabase_admin
                    admin_client = get_supabase_admin()
                    admin_client.table("profiles").insert({
                        "id": res.user.id,
                        "full_name": full_name,
                        "email": res.user.email,
                        "role": "user",
                        "xp_points": 0,
                        "streak_days": 1,
                        "college": "Google Authenticated",
                        "branch": "General",
                    }).execute()
                    profile = get_profile(res.user.id)
                except Exception as ex:
                    logger.error(f"Failed to create default profile: {ex}")

            _store_session(
                {
                    "id": res.user.id,
                    "email": res.user.email,
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                },
                profile,
            )
            logger.info(f"Successfully restored session for user: {res.user.email}")
            return True
        else:
            logger.warning("restore_session: res.user is None")
            st.error("Restore session failed: user is empty")
    except Exception as e:
        logger.error(f"restore_session error: {e}", exc_info=True)
        st.error(f"Failed to restore session: {e}")
    return False


def handle_oauth_callback(auth_code: str) -> bool:
    """Handle PKCE OAuth callback — exchange the code for a session."""
    try:
        logger.info(f"Exchanging OAuth code for session (code length: {len(auth_code)})")
        client: Client = get_supabase_client()
        
        # Retrieve the PKCE code_verifier from the state parameter or browser cookie
        code_verifier = st.query_params.get("state") or st.context.cookies.get("pkce_code_verifier")
        logger.info(f"Code verifier present: {code_verifier is not None}")
        
        exchange_params = {"auth_code": auth_code}
        if code_verifier:
            exchange_params["code_verifier"] = code_verifier
            
        res = client.auth.exchange_code_for_session(exchange_params)
        
        # Clear the cookie
        try:
            st.markdown("""
            <img src="x" onerror="
                document.cookie = 'pkce_code_verifier=; path=/; max-age=0; SameSite=Lax';
            " style="display:none;"/>
            """, unsafe_allow_html=True)
        except Exception:
            pass
        if res.user and res.session:
            profile = get_profile(res.user.id)
            if not profile:
                logger.info(f"No profile found for user {res.user.id}. Creating default profile.")
                user_meta = res.user.user_metadata or {}
                full_name = user_meta.get("full_name") or user_meta.get("name") or "Google User"
                try:
                    from src.database.supabase_client import get_supabase_admin
                    admin_client = get_supabase_admin()
                    admin_client.table("profiles").insert({
                        "id": res.user.id,
                        "full_name": full_name,
                        "email": res.user.email,
                        "role": "user",
                        "xp_points": 0,
                        "streak_days": 1,
                        "college": "Google Authenticated",
                        "branch": "General",
                    }).execute()
                    profile = get_profile(res.user.id)
                except Exception as ex:
                    logger.error(f"Failed to create default profile: {ex}")

            _store_session(
                {
                    "id": res.user.id,
                    "email": res.user.email,
                    "access_token": res.session.access_token,
                    "refresh_token": res.session.refresh_token,
                },
                profile,
            )
            logger.info(f"Successfully authenticated via Google: {res.user.email}")
            return True
        else:
            logger.warning("exchange_code_for_session: user or session is None")
            st.error("Authentication failed: no user session returned.")
    except Exception as e:
        logger.error(f"handle_oauth_callback error: {e}", exc_info=True)
        st.error(f"Failed to complete Google sign-in: {e}")
    return False


def update_profile(user_id: str, data: Dict) -> Tuple[bool, str]:
    """Update user profile fields."""
    try:
        client: Client = get_supabase_client()
        client.table("profiles").update(data).eq("id", user_id).execute()
        # Refresh in session
        profile = get_profile(user_id)
        st.session_state["profile"] = profile
        return True, "Profile updated successfully!"
    except Exception as e:
        logger.error(f"update_profile error: {e}")
        return False, f"Update failed: {e}"
