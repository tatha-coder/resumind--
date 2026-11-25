"""
Resumind AI - Supabase Authentication & Database Client
Manages user sign-in, sign-up, password reset, profile sync,
and persistence of resume analyses and mock interview attempts.
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from dotenv import load_dotenv
from supabase import Client, create_client

ROOT_DIR = Path(__file__).resolve().parent
load_dotenv(dotenv_path=ROOT_DIR / ".env")


def get_supabase_config() -> Tuple[str, str]:
    """Return Supabase project URL and publishable key from environment or Streamlit secrets."""
    url = os.getenv("SUPABASE_URL", "").strip()
    key = (
        os.getenv("SUPABASE_PUBLISHABLE_KEY", "").strip()
        or os.getenv("SUPABASE_ANON_KEY", "").strip()
    )

    if not url or not key:
        try:
            import streamlit as st
            url = url or str(st.secrets.get("SUPABASE_URL", "")).strip()
            key = key or str(
                st.secrets.get("SUPABASE_PUBLISHABLE_KEY")
                or st.secrets.get("SUPABASE_ANON_KEY", "")
            ).strip()
        except Exception:
            pass

    if not url or not key:
        raise RuntimeError(
            "Supabase credentials missing. Set SUPABASE_URL and SUPABASE_PUBLISHABLE_KEY in .env."
        )
    return url, key


def get_client(
    access_token: Optional[str] = None,
    refresh_token: Optional[str] = None,
) -> Client:
    """Create a fresh per-request Supabase client, optionally authenticated with user tokens."""
    url, key = get_supabase_config()
    client = create_client(url, key)
    if access_token and refresh_token:
        client.auth.set_session(access_token, refresh_token)
    return client


def _extract_user_info(user_obj: Any) -> Dict[str, str]:
    """Normalize a Supabase Auth User object into a plain dictionary."""
    if user_obj is None:
        return {}
    meta = getattr(user_obj, "user_metadata", None) or {}
    email = getattr(user_obj, "email", "") or ""
    full_name = str(meta.get("full_name", "") or "").strip()
    if not full_name and email:
        full_name = email.split("@")[0]
    return {
        "id": str(getattr(user_obj, "id", "")),
        "email": email,
        "full_name": full_name,
    }


def _friendly_auth_error(err: Exception) -> str:
    """Convert Supabase Auth exceptions into clear user-facing messages."""
    msg = str(err)
    lower = msg.lower()
    if "invalid login credentials" in lower:
        return "Incorrect email or password. Please try again."
    if "email not confirmed" in lower:
        return "Your email is not confirmed yet. Please check your inbox and click the confirmation link."
    if "user already registered" in lower or "already been registered" in lower:
        return "An account with this email already exists. Please sign in instead."
    if "password should be at least" in lower:
        return "Password must be at least 6 characters long."
    if "rate limit" in lower or "too many requests" in lower:
        return "Too many attempts. Please wait a moment and try again."
    return msg


def sign_in_with_email(email: str, password: str) -> Dict[str, Any]:
    """Authenticate an existing user with email and password."""
    try:
        client = get_client()
        res = client.auth.sign_in_with_password(
            {"email": email.strip(), "password": password}
        )
        if not res.session or not res.user:
            return {"ok": False, "error": "Unable to start a session. Please try again."}
        return {
            "ok": True,
            "user": _extract_user_info(res.user),
            "access_token": res.session.access_token,
            "refresh_token": res.session.refresh_token,
        }
    except Exception as exc:
        return {"ok": False, "error": _friendly_auth_error(exc)}


def sign_up_with_email(email: str, password: str, full_name: str = "") -> Dict[str, Any]:
    """Register a new user account in Supabase Auth."""
    try:
        client = get_client()
        res = client.auth.sign_up(
            {
                "email": email.strip(),
                "password": password,
                "options": {"data": {"full_name": full_name.strip()}},
            }
        )
        user_info = _extract_user_info(res.user)
        if res.session and res.user:
            return {
                "ok": True,
                "needs_email_confirmation": False,
                "user": user_info,
                "access_token": res.session.access_token,
                "refresh_token": res.session.refresh_token,
            }
        if res.user:
            return {
                "ok": True,
                "needs_email_confirmation": True,
                "user": user_info,
            }
        return {"ok": False, "error": "Sign-up did not return a user record."}
    except Exception as exc:
        return {"ok": False, "error": _friendly_auth_error(exc)}


def send_password_reset(email: str) -> Dict[str, Any]:
    """Trigger a password reset email via Supabase Auth."""
    try:
        client = get_client()
        client.auth.reset_password_for_email(email.strip())
        return {"ok": True}
    except Exception as exc:
        return {"ok": False, "error": _friendly_auth_error(exc)}


def sign_out_session(access_token: str, refresh_token: str) -> None:
    """Sign out the active Supabase session cleanly."""
    try:
        client = get_client(access_token, refresh_token)
        client.auth.sign_out()
    except Exception:
        pass


def get_profile(
    user_id: str,
    access_token: str,
    refresh_token: str,
) -> Optional[Dict[str, Any]]:
    """Fetch the authenticated user's profile row from public.profiles."""
    try:
        client = get_client(access_token, refresh_token)
        resp = (
            client.table("profiles")
            .select("id, full_name, email, created_at")
            .eq("id", user_id)
            .maybe_single()
            .execute()
        )
        return resp.data if resp else None
    except Exception:
        return None


def save_resume_analysis(
    user_id: str,
    access_token: str,
    refresh_token: str,
    file_name: str,
    candidate: Dict[str, Any],
    soura_result: Dict[str, Any],
    match_data: Dict[str, Any],
    job_description: str = "",
) -> Optional[str]:
    """Persist a completed resume analysis to public.resume_analyses and return its UUID."""
    try:
        client = get_client(access_token, refresh_token)
        payload = {
            "user_id": user_id,
            "file_name": str(file_name or "resume.pdf"),
            "candidate_name": str(candidate.get("name", "Candidate")),
            "candidate_email": str(candidate.get("email", "")),
            "career_category": str(soura_result.get("resume_category", "")),
            "job_description": str(job_description or ""),
            "match_score": match_data.get("match_score"),
            "matched_skills": match_data.get("matched_skills", []),
            "missing_skills": match_data.get("missing_skills", []),
            "detected_skills": soura_result.get("skills", {}),
            "neural_predictions": soura_result.get("trained_skill_predictions", [])[:20],
            "ai_analysis": str(soura_result.get("ai_analysis", "")),
        }
        resp = client.table("resume_analyses").insert(payload).execute()
        if resp.data and isinstance(resp.data, list):
            return str(resp.data[0].get("id", "")) or None
        return None
    except Exception:
        return None


def list_resume_analyses(
    user_id: str,
    access_token: str,
    refresh_token: str,
    limit: int = 15,
) -> List[Dict[str, Any]]:
    """List saved resume analyses for the authenticated user, newest first."""
    try:
        client = get_client(access_token, refresh_token)
        resp = (
            client.table("resume_analyses")
            .select(
                "id, file_name, candidate_name, candidate_email, career_category, "
                "job_description, match_score, matched_skills, missing_skills, "
                "detected_skills, neural_predictions, ai_analysis, created_at"
            )
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return resp.data or []
    except Exception:
        return []


def delete_resume_analysis(
    analysis_id: str,
    access_token: str,
    refresh_token: str,
) -> bool:
    """Delete a saved resume analysis belonging to the authenticated user."""
    try:
        client = get_client(access_token, refresh_token)
        client.table("resume_analyses").delete().eq("id", analysis_id).execute()
        return True
    except Exception:
        return False


def save_interview_attempt(
    user_id: str,
    access_token: str,
    refresh_token: str,
    candidate_name: str,
    focus_mode: str,
    eval_res: Dict[str, Any],
    analysis_id: Optional[str] = None,
) -> Optional[str]:
    """Persist a completed mock interview score to public.interview_attempts."""
    try:
        client = get_client(access_token, refresh_token)
        payload = {
            "user_id": user_id,
            "analysis_id": analysis_id,
            "candidate_name": str(candidate_name or "Candidate"),
            "focus_mode": str(focus_mode or "Balanced Mock Interview"),
            "score_pct": float(eval_res.get("score_pct", 0.0)),
            "correct_count": int(eval_res.get("correct_count", 0)),
            "total_questions": int(eval_res.get("total", 0)),
            "readiness_tier": str(eval_res.get("tier", "N/A")),
            "weak_skills": eval_res.get("weak_skills", []),
            "skill_stats": eval_res.get("skill_stats", {}),
        }
        resp = client.table("interview_attempts").insert(payload).execute()
        if resp.data and isinstance(resp.data, list):
            return str(resp.data[0].get("id", "")) or None
        return None
    except Exception:
        return None


def list_interview_attempts(
    user_id: str,
    access_token: str,
    refresh_token: str,
    limit: int = 15,
) -> List[Dict[str, Any]]:
    """List saved mock interview attempts for the authenticated user, newest first."""
    try:
        client = get_client(access_token, refresh_token)
        resp = (
            client.table("interview_attempts")
            .select(
                "id, candidate_name, focus_mode, score_pct, correct_count, "
                "total_questions, readiness_tier, weak_skills, created_at"
            )
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return resp.data or []
    except Exception:
        return []
