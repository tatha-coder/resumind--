import io
import os
import re
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from xml.sax.saxutils import escape

from fastapi import FastAPI, File, Form, Header, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel
import pymupdf

# Ensure project root is on sys.path so all local engines import cleanly on Vercel & locally
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from ai_engine.inference import predict_match, predict_skills
from ai_engine.resume_observer import SKILL_DATABASE
from config import APP_NAME, DEVICE
from interview_engine import (
    evaluate_test,
    generate_interview_pdf_report,
    generate_interview_test,
)
from job_predictor import JOB_CATALOG, predict_job_options
from llm_analyzer import analyse_resume, analyze_resume
from matcher import calculate_match, extract_skills_by_category
from supabase_client import (
    delete_resume_analysis,
    get_client,
    get_profile,
    get_supabase_config,
    list_interview_attempts,
    list_resume_analyses,
    save_interview_attempt,
    save_resume_analysis,
    send_password_reset,
    sign_in_with_email,
    sign_out_session,
    sign_up_with_email,
)

app = FastAPI(
    title="Resumind AI",
    description="Executive Resume Intelligence Platform",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==========================================================
# HELPERS
# ==========================================================

def _extract_candidate_info(text: str) -> Dict[str, str]:
    email_match = re.search(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b", text)
    phone_match = re.search(
        r"(?:\+?\d{1,3}[\s.-]?)?(?:\(?\d{2,5}\)?[\s.-]?)?\d{3,5}[\s.-]?\d{4,5}",
        text,
    )
    linkedin_match = re.search(
        r"(?:https?://)?(?:www\.)?linkedin\.com/(?:in|pub)/[a-zA-Z0-9_\-]+",
        text,
        re.IGNORECASE,
    )
    github_match = re.search(
        r"(?:https?://)?(?:www\.)?github\.com/[a-zA-Z0-9_\-]+",
        text,
        re.IGNORECASE,
    )
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    candidate_name = "Candidate"
    excluded_words = [
        "resume", "curriculum vitae", "cv", "email", "phone", "mobile",
        "linkedin", "github", "portfolio", "address", "profile", "summary",
        "objective", "education", "experience", "skills", "developer", "engineer",
    ]
    for line in lines[:10]:
        clean_line = re.sub(r"^[•*|✦\s\d\.-]+", "", line).strip()
        words = clean_line.split()
        if (
            1 <= len(words) <= 4
            and len(clean_line) <= 45
            and not re.search(r"[@\d:/\\{}<>]", clean_line)
            and not any(word in clean_line.lower() for word in excluded_words)
            and any(c.isalpha() for c in clean_line)
        ):
            candidate_name = clean_line
            break

    phone_str = "Not found"
    if phone_match:
        digits = re.sub(r"\D", "", phone_match.group(0))
        if 10 <= len(digits) <= 13:
            phone_str = phone_match.group(0).strip()

    return {
        "name": candidate_name,
        "email": email_match.group(0) if email_match else "Not found",
        "phone": phone_str,
        "linkedin": linkedin_match.group(0) if linkedin_match else "",
        "github": github_match.group(0) if github_match else "",
    }


def _extract_job_skills(job_description: str) -> List[str]:
    found: List[str] = []
    for _, skills in SKILL_DATABASE.items():
        for skill in skills:
            pattern = r"(?<![a-zA-Z0-9])" + re.escape(skill) + r"(?![a-zA-Z0-9])"
            if re.search(pattern, job_description, re.IGNORECASE):
                found.append(skill)
    return list(dict.fromkeys(found))


def _calculate_job_match_payload(soura_result: Dict[str, Any], job_description: str) -> Dict[str, Any]:
    resume_skills: List[str] = []
    for category_skills in (soura_result.get("skills") or {}).values():
        for skill in category_skills:
            if skill not in resume_skills:
                resume_skills.append(skill)

    for pred in soura_result.get("trained_skill_predictions", []):
        if pred.get("predicted_present") and pred.get("skill") not in resume_skills:
            resume_skills.append(pred["skill"])

    if not job_description.strip():
        return {
            "resume_skills": resume_skills,
            "required_skills": [],
            "matched_skills": [],
            "missing_skills": [],
            "match_score": None,
        }

    required_skills = _extract_job_skills(job_description)
    resume_set = {s.lower() for s in resume_skills}
    matched = [s for s in required_skills if s.lower() in resume_set]
    missing = [s for s in required_skills if s.lower() not in resume_set]
    score = round(len(matched) / len(required_skills) * 100, 2) if required_skills else None
    return {
        "resume_skills": resume_skills,
        "required_skills": required_skills,
        "matched_skills": matched,
        "missing_skills": missing,
        "match_score": score,
    }


def _resolve_auth_user(authorization: str, refresh_token: str) -> Optional[Dict[str, str]]:
    """Verify the Bearer JWT with Supabase Auth and return user info + tokens if valid."""
    if not authorization or not authorization.lower().startswith("bearer "):
        return None
    access_token = authorization.split(" ", 1)[1].strip()
    if not access_token or not refresh_token:
        return None
    try:
        client = get_client()
        user_resp = client.auth.get_user(access_token)
        if not user_resp or not user_resp.user:
            return None
        user_obj = user_resp.user
        meta = getattr(user_obj, "user_metadata", None) or {}
        email = getattr(user_obj, "email", "") or ""
        full_name = str(meta.get("full_name", "") or "").strip() or (email.split("@")[0] if email else "Member")
        return {
            "id": str(user_obj.id),
            "email": email,
            "full_name": full_name,
            "access_token": access_token,
            "refresh_token": refresh_token,
        }
    except Exception:
        return None


def _build_resume_pdf_bytes(payload: Dict[str, Any]) -> bytes:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

    buffer = io.BytesIO()
    document = SimpleDocTemplate(
        buffer, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40
    )
    styles = getSampleStyleSheet()
    story = [
        Paragraph("<b>RESUMIND AI</b>", styles["Title"]),
        Paragraph("Resumind AI - Executive Career & Skills Analysis Report", styles["Heading2"]),
        Spacer(1, 16),
    ]

    candidate = payload.get("candidate") or {}
    soura = payload.get("soura_result") or {}
    match = payload.get("match_data") or {}

    for label, value in [
        ("Candidate", candidate.get("name", "Candidate")),
        ("Email", candidate.get("email", "Not found")),
        ("Phone", candidate.get("phone", "Not found")),
        ("Career category", soura.get("resume_category", "Technical Professional")),
    ]:
        story.append(Paragraph(f"<b>{label}:</b> {escape(str(value))}", styles["Normal"]))

    story.append(Spacer(1, 12))
    if match.get("match_score") is not None:
        story.append(Paragraph(f"<b>Job skill overlap:</b> {float(match['match_score']):.1f}%", styles["Heading2"]))

    def add_section(title: str, content: Any):
        story.append(Paragraph(title, styles["Heading2"]))
        if isinstance(content, dict):
            if not content:
                story.append(Paragraph("No information detected.", styles["Normal"]))
            for category, values in content.items():
                story.append(
                    Paragraph(
                        f"<b>{escape(str(category))}:</b> {escape(', '.join(map(str, values)))}",
                        styles["Normal"],
                    )
                )
        elif isinstance(content, list):
            if not content:
                story.append(Paragraph("No information detected.", styles["Normal"]))
            for item in content:
                story.append(Paragraph(escape(str(item)), styles["Normal"]))
        elif content:
            for line in str(content).splitlines():
                if line.strip():
                    story.append(Paragraph(escape(line), styles["Normal"]))
        else:
            story.append(Paragraph("No information detected.", styles["Normal"]))
        story.append(Spacer(1, 10))

    edu = soura.get("education") or {}
    exp = soura.get("experience") or {}
    add_section("Professional Summary", soura.get("professional_summary", ""))
    add_section("Education", edu.get("section_text", "") if isinstance(edu, dict) else edu)
    add_section("Work Experience", exp.get("section_text", "") if isinstance(exp, dict) else exp)
    add_section("Detected Skills", soura.get("skills", {}))
    add_section("Projects", soura.get("projects", []))
    add_section("Certifications", soura.get("certifications", []))
    add_section("Matched Skills", match.get("matched_skills", []))
    add_section("Missing Skills", match.get("missing_skills", []))
    add_section("Executive AI Analysis", soura.get("ai_analysis", ""))

    document.build(story)
    buffer.seek(0)
    return buffer.getvalue()


# ==========================================================
# REQUEST MODELS
# ==========================================================

class SignInRequest(BaseModel):
    email: str
    password: str


class SignUpRequest(BaseModel):
    full_name: str = ""
    email: str
    password: str


class ResetPasswordRequest(BaseModel):
    email: str


class CareerPathsRequest(BaseModel):
    candidate_skills: List[str] = []
    resume_category: Optional[str] = None
    top_n: int = 20


class InterviewGenerateRequest(BaseModel):
    candidate_skills: List[str] = []
    resume_category: Optional[str] = "IT & SOFTWARE"
    num_questions: int = 5
    focus_mode: str = "Balanced Mock Interview"


class InterviewEvaluateRequest(BaseModel):
    questions: List[Dict[str, Any]]
    user_answers: Dict[str, int]
    candidate_name: str = "Candidate"
    focus_mode: str = "Balanced Mock Interview"
    analysis_id: Optional[str] = None


class InterviewPdfRequest(BaseModel):
    candidate_name: str = "Candidate"
    evaluation_result: Dict[str, Any]


# ==========================================================
# API ROUTES
# ==========================================================

@app.get("/health")
@app.get("/api/health")
def health_check():
    supabase_configured = False
    try:
        get_supabase_config()
        supabase_configured = True
    except Exception:
        pass
    return {
        "status": "healthy",
        "service": APP_NAME,
        "version": "2.0.0",
        "device": str(DEVICE),
        "engine": "Custom PyTorch Neural Architecture (SkillNet & MatchNet)",
        "supabase_configured": supabase_configured,
    }


@app.post("/api/auth/signin")
def api_signin(req: SignInRequest):
    res = sign_in_with_email(req.email, req.password)
    if not res.get("ok"):
        raise HTTPException(status_code=401, detail=res.get("error", "Sign-in failed."))
    return res


@app.post("/api/auth/signup")
def api_signup(req: SignUpRequest):
    if len(req.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters long.")
    res = sign_up_with_email(req.email, req.password, req.full_name)
    if not res.get("ok"):
        raise HTTPException(status_code=400, detail=res.get("error", "Sign-up failed."))
    return res


@app.post("/api/auth/reset-password")
def api_reset_password(req: ResetPasswordRequest):
    res = send_password_reset(req.email)
    if not res.get("ok"):
        raise HTTPException(status_code=400, detail=res.get("error", "Failed to send reset link."))
    return {"ok": True}


@app.post("/api/auth/signout")
def api_signout(
    authorization: str = Header(default=""),
    x_refresh_token: str = Header(default=""),
):
    if authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()
        sign_out_session(token, x_refresh_token)
    return {"ok": True}


@app.get("/api/account/history")
def api_account_history(
    authorization: str = Header(default=""),
    x_refresh_token: str = Header(default=""),
):
    auth = _resolve_auth_user(authorization, x_refresh_token)
    if not auth:
        raise HTTPException(status_code=401, detail="Authentication required.")
    profile = get_profile(auth["id"], auth["access_token"], auth["refresh_token"])
    analyses = list_resume_analyses(auth["id"], auth["access_token"], auth["refresh_token"])
    interviews = list_interview_attempts(auth["id"], auth["access_token"], auth["refresh_token"])
    return {
        "user": {
            "id": auth["id"],
            "email": (profile or {}).get("email") or auth["email"],
            "full_name": (profile or {}).get("full_name") or auth["full_name"],
        },
        "analyses": analyses,
        "interviews": interviews,
    }


@app.delete("/api/account/analyses/{analysis_id}")
def api_delete_analysis(
    analysis_id: str,
    authorization: str = Header(default=""),
    x_refresh_token: str = Header(default=""),
):
    auth = _resolve_auth_user(authorization, x_refresh_token)
    if not auth:
        raise HTTPException(status_code=401, detail="Authentication required.")
    ok = delete_resume_analysis(analysis_id, auth["access_token"], auth["refresh_token"])
    return {"ok": ok}


@app.post("/api/analyze")
@app.post("/analyze")
async def analyze_endpoint(
    request: Request,
    file: Optional[UploadFile] = File(None),
    job_description: Optional[str] = Form(None),
    authorization: str = Header(default=""),
    x_refresh_token: str = Header(default=""),
):
    resume_text = ""
    filename = "resume.pdf"
    jd_text = (job_description or "").strip()
    pdf_bytes: Optional[bytes] = None

    if file:
        filename = file.filename or "resume.pdf"
        pdf_bytes = await file.read()
        try:
            parts: List[str] = []
            with pymupdf.open(stream=pdf_bytes, filetype="pdf") as doc:
                for page in doc:
                    txt = page.get_text("text", sort=True)
                    if not txt or len(txt.strip()) < 15:
                        blocks = page.get_text("blocks")
                        txt = "\n".join(b[4] for b in blocks if len(b) > 4 and str(b[4]).strip())
                    if txt.strip():
                        parts.append(txt)
            resume_text = "\n".join(parts).replace("\xa0", " ").replace("\x00", " ").strip()
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"Failed to extract text from PDF: {exc}")
    else:
        try:
            body = await request.json()
            resume_text = str(body.get("resume_text", "")).strip()
            jd_text = str(body.get("job_description", "") or jd_text).strip()
        except Exception:
            pass

    if not resume_text:
        raise HTTPException(
            status_code=400,
            detail="No readable text found in resume. Scanned image-only PDFs require OCR.",
        )

    candidate = _extract_candidate_info(resume_text)
    soura_result: Dict[str, Any]

    if pdf_bytes is not None:
        with tempfile.NamedTemporaryFile(
            dir=tempfile.gettempdir(), suffix=".pdf", delete=False
        ) as tmp:
            tmp.write(pdf_bytes)
            tmp_path = Path(tmp.name)
        try:
            soura_result = analyze_resume(tmp_path, jd_text)
        finally:
            tmp_path.unlink(missing_ok=True)
    else:
        preds = predict_skills(resume_text)
        skills_by_cat = extract_skills_by_category(resume_text)
        ai_report = analyse_resume(resume_text, jd_text)
        soura_result = {
            "engine": "Resumind Custom PyTorch AI",
            "file_name": filename,
            "resume_category": "IT" if skills_by_cat else "Professional",
            "personal_information": candidate,
            "professional_summary": "",
            "career_objective": "",
            "education": {},
            "experience": {},
            "skills": skills_by_cat,
            "projects": [],
            "certifications": [],
            "achievements": [],
            "languages": [],
            "trained_skill_predictions": preds,
            "trained_model_status": f"PyTorch SkillNet Active ({DEVICE})",
            "ai_analysis": ai_report,
        }

    match_data = _calculate_job_match_payload(soura_result, jd_text)

    # Also compute deterministic ATS / Neural score when JD provided
    ats_score = 75
    neural_match_score = None
    if jd_text:
        try:
            det_match = calculate_match(resume_text, jd_text)
            ats_score = det_match.get("ats_score", 75) or 75
        except Exception:
            pass
        try:
            neural_match_score = predict_match(resume_text, jd_text)
        except Exception:
            pass

    candidate_skills = list(match_data.get("resume_skills") or [])
    predicted_roles = predict_job_options(
        candidate_skills=candidate_skills,
        resume_category=soura_result.get("resume_category"),
        top_n=3,
    )

    saved_id = None
    auth = _resolve_auth_user(authorization, x_refresh_token)
    if auth:
        saved_id = save_resume_analysis(
            user_id=auth["id"],
            access_token=auth["access_token"],
            refresh_token=auth["refresh_token"],
            file_name=filename,
            candidate=candidate,
            soura_result=soura_result,
            match_data=match_data,
            job_description=jd_text,
        )

    return {
        "success": True,
        "saved_id": saved_id,
        "filename": filename,
        "created_at": datetime.now().strftime("%d %b %Y, %I:%M %p"),
        "candidate": candidate,
        "soura_result": soura_result,
        "match_data": match_data,
        "ats_score": ats_score,
        "neural_match_score": neural_match_score,
        "predicted_roles": predicted_roles,
        # Backward-compatible flat fields
        "match_score": match_data.get("match_score") or neural_match_score or 0,
        "matched_skills": match_data.get("matched_skills", []),
        "missing_skills": match_data.get("missing_skills", []),
        "ai_analysis": soura_result.get("ai_analysis", ""),
    }


@app.post("/api/career-paths")
def api_career_paths(req: CareerPathsRequest):
    skills = [s for s in req.candidate_skills if s]
    has_skills = bool(skills)
    roles = predict_job_options(
        candidate_skills=skills if has_skills else ["Python", "SQL", "Git"],
        resume_category=req.resume_category,
        top_n=max(1, min(len(JOB_CATALOG), req.top_n)),
    )
    categories = ["All Domains"] + sorted(list({j["category"] for j in JOB_CATALOG}))
    return {
        "roles": roles,
        "categories": categories,
        "personalized": has_skills,
    }


@app.get("/api/interview/skills")
def api_interview_skills():
    all_skills = sorted({s for slist in SKILL_DATABASE.values() for s in slist})
    return {"skills": all_skills}


@app.post("/api/interview/generate")
def api_interview_generate(req: InterviewGenerateRequest):
    questions = generate_interview_test(
        candidate_skills=req.candidate_skills or ["Python", "SQL", "Git", "Problem Solving"],
        resume_category=req.resume_category,
        num_questions=max(1, min(15, req.num_questions)),
        focus_mode=req.focus_mode,
    )
    return {"questions": questions}


@app.post("/api/interview/evaluate")
def api_interview_evaluate(
    req: InterviewEvaluateRequest,
    authorization: str = Header(default=""),
    x_refresh_token: str = Header(default=""),
):
    eval_res = evaluate_test(req.questions, req.user_answers)
    saved_id = None
    auth = _resolve_auth_user(authorization, x_refresh_token)
    if auth:
        saved_id = save_interview_attempt(
            user_id=auth["id"],
            access_token=auth["access_token"],
            refresh_token=auth["refresh_token"],
            candidate_name=req.candidate_name,
            focus_mode=req.focus_mode,
            eval_res=eval_res,
            analysis_id=req.analysis_id,
        )
    return {"evaluation": eval_res, "saved_id": saved_id}


@app.post("/api/report/resume-pdf")
def api_report_resume_pdf(payload: Dict[str, Any]):
    pdf_bytes = _build_resume_pdf_bytes(payload)
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="Resumind_AI_Report.pdf"'},
    )


@app.post("/api/report/interview-pdf")
def api_report_interview_pdf(req: InterviewPdfRequest):
    pdf_bytes = generate_interview_pdf_report(req.candidate_name, req.evaluation_result)
    if not pdf_bytes:
        raise HTTPException(status_code=500, detail="Failed to generate interview PDF report.")
    safe_name = re.sub(r"[^A-Za-z0-9_-]+", "_", req.candidate_name or "Candidate")
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="Interview_Readiness_{safe_name}.pdf"'},
    )


# ==========================================================
# WEB FRONTEND (MATCHES STREAMLIT SAGE / OAT / OLIVE UI)
# ==========================================================

HTML_CONTENT = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Resumind AI — Resume Intelligence</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,300..700;1,9..40,400&family=Outfit:wght@500;600;700;800;900&family=Space+Grotesk:wght@500;600;700&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg: #EDEAE2;
      --bg-soft: #F5F2EB;
      --sage: #A7B099;
      --sage-deep: #4A5536;
      --sage-tint: #E5EAD9;
      --ink: #3A2C23;
      --espresso-dark: #2A2019;
      --muted: #73665C;
      --card: #FAF8F4;
      --border: #DCD4C6;
      --terracotta: #9C5F53;
      --terracotta-bg: #F5E8E4;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    html { scroll-behavior: smooth; }
    body {
      background-color: var(--bg);
      color: var(--ink);
      font-family: 'DM Sans', -apple-system, sans-serif;
      -webkit-font-smoothing: antialiased;
      line-height: 1.6;
    }
    .page-shell {
      max-width: 1220px;
      margin: 0 auto;
      padding: 18px 24px 42px;
    }

    /* TOP HEADER */
    .topbar {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 16px;
      flex-wrap: wrap;
      margin-bottom: 18px;
    }
    .brand {
      display: inline-flex;
      align-items: center;
      gap: 10px;
      font-family: 'Outfit', sans-serif;
      font-size: 21px;
      font-weight: 800;
      letter-spacing: -0.02em;
      color: var(--ink);
      cursor: pointer;
      white-space: nowrap;
      text-decoration: none;
    }
    .brand-badge {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 34px;
      height: 34px;
      border-radius: 10px;
      background: var(--ink);
      color: #F6F3EB;
      font-family: 'Outfit', sans-serif;
      font-weight: 900;
      font-size: 18px;
    }
    .brand-accent { color: var(--sage-deep); }

    .nav-dock {
      display: inline-flex;
      align-items: center;
      flex-wrap: wrap;
      gap: 6px;
      background: #F7F4EC;
      border: 1px solid #D7D0C1;
      border-radius: 999px;
      padding: 6px 8px;
      box-shadow: 0 8px 22px rgba(58, 44, 35, 0.06);
    }
    .nav-btn {
      border: 1px solid #D4CCBA;
      background: #EDEAE2;
      color: #3A2C23;
      border-radius: 999px;
      padding: 8px 14px;
      font-family: 'Outfit', sans-serif;
      font-weight: 700;
      font-size: 12px;
      letter-spacing: 0.05em;
      cursor: pointer;
      white-space: nowrap;
      transition: all 0.2s cubic-bezier(0.22, 1, 0.36, 1);
    }
    .nav-btn:hover {
      background: #DFE6D3;
      color: #2B3421;
      border-color: #939E81;
      transform: translateY(-1px);
    }
    .nav-btn.active {
      background: linear-gradient(135deg, #4A5536 0%, #2F3820 100%);
      color: #F7F4EC;
      border-color: #2F3820;
      box-shadow: 0 5px 14px rgba(47, 56, 32, 0.25);
    }

    /* HERO */
    .hero {
      text-align: center;
      background: linear-gradient(155deg, #B2BAA5 0%, #9CA58E 100%);
      border: 1px solid #969F88;
      border-radius: 28px;
      padding: 46px 28px 40px;
      margin: 6px 0 24px;
      box-shadow: 0 10px 30px rgba(58, 44, 35, 0.06);
    }
    .hero-tag {
      display: inline-block;
      background: #3A2C23;
      border: 1px solid #2A2019;
      border-radius: 999px;
      padding: 6px 16px;
      color: #F5F2EB;
      font-size: 11px;
      font-weight: 700;
      letter-spacing: .12em;
      text-transform: uppercase;
    }
    .hero h1 {
      font-family: 'Outfit', sans-serif;
      font-size: clamp(38px, 6vw, 68px);
      line-height: 0.98;
      letter-spacing: -0.04em;
      font-weight: 900;
      color: #F7F4EC;
      margin: 18px 0 14px;
    }
    .hero h1 em { color: #2E221A; font-style: normal; }
    .hero p {
      max-width: 640px;
      margin: auto;
      color: #2E221A;
      font-size: 15px;
      font-weight: 500;
      line-height: 1.65;
      opacity: 0.88;
    }

    /* BUTTONS */
    .btn-primary {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      background: linear-gradient(135deg, #3A2C23 0%, #2A2019 100%);
      color: #F6F3EB;
      border: none;
      border-radius: 999px;
      padding: 13px 26px;
      font-family: 'Outfit', 'DM Sans', sans-serif;
      font-weight: 700;
      font-size: 13.5px;
      letter-spacing: .05em;
      cursor: pointer;
      box-shadow: 0 6px 18px rgba(42, 32, 25, 0.18);
      transition: all 0.22s cubic-bezier(0.22, 1, 0.36, 1);
      text-decoration: none;
    }
    .btn-primary:hover {
      background: linear-gradient(135deg, #4A5536 0%, #343D25 100%);
      box-shadow: 0 8px 22px rgba(74, 85, 54, 0.28);
      transform: translateY(-1.5px);
    }
    .btn-primary:disabled { opacity: 0.6; cursor: not-allowed; transform: none; }
    .btn-secondary {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 6px;
      background: var(--card);
      color: var(--ink);
      border: 1px solid #CFC6B6;
      border-radius: 999px;
      padding: 10px 18px;
      font-family: 'Outfit', 'DM Sans', sans-serif;
      font-weight: 700;
      font-size: 13px;
      letter-spacing: .04em;
      cursor: pointer;
      text-decoration: none;
      transition: all 0.2s ease;
    }
    .btn-secondary:hover {
      background: var(--ink);
      color: #F6F3EB;
      border-color: var(--ink);
    }

    /* SCROLL POP-UP ANIMATIONS */
    .scroll-pop {
      transition: opacity 0.6s cubic-bezier(0.22, 1, 0.36, 1),
                  transform 0.6s cubic-bezier(0.22, 1, 0.36, 1),
                  box-shadow 0.25s ease,
                  border-color 0.25s ease;
      will-change: opacity, transform;
    }
    .scroll-pop-delay-1 { transition-delay: 0.07s; }
    .scroll-pop-delay-2 { transition-delay: 0.14s; }
    .scroll-pop.scroll-hidden-bottom { opacity: 0; transform: translateY(44px) scale(0.93); }
    .scroll-pop.scroll-hidden-top { opacity: 0; transform: translateY(-36px) scale(0.93); }
    .scroll-pop.scroll-visible { opacity: 1; transform: translateY(0) scale(1); }

    /* TYPOGRAPHY & CARDS */
    .section-tag {
      color: var(--sage-deep);
      font-size: 11px;
      font-weight: 700;
      letter-spacing: .14em;
      text-transform: uppercase;
      display: inline-block;
    }
    .section-heading {
      font-family: 'Outfit', sans-serif;
      font-size: 32px;
      font-weight: 800;
      letter-spacing: -0.03em;
      line-height: 1.1;
      color: var(--ink);
      margin: 8px 0 12px;
    }
    .panel-badge {
      display: inline-block;
      background: var(--sage-tint);
      color: var(--sage-deep);
      border: 1px solid #C6D0B4;
      border-radius: 999px;
      padding: 3px 11px;
      font-size: 11px;
      font-weight: 700;
      letter-spacing: .08em;
      margin-bottom: 6px;
    }
    .grid-3 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }
    .grid-2 { display: grid; grid-template-columns: repeat(2, 1fr); gap: 18px; }
    .grid-4 { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; }
    @media (max-width: 900px) { .grid-3, .grid-4 { grid-template-columns: repeat(2, 1fr); } }
    @media (max-width: 680px) { .grid-3, .grid-2, .grid-4 { grid-template-columns: 1fr; } }

    .card {
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 22px;
      padding: 24px;
      box-shadow: 0 4px 16px rgba(58, 44, 35, 0.04);
    }
    .feature-card:hover, .pipeline-card:hover {
      transform: translateY(-4px) scale(1.01);
      border-color: #9CA58E;
      box-shadow: 0 14px 28px rgba(58, 44, 35, 0.09);
    }
    .feature-card h3, .pipeline-card h4 {
      font-family: 'Outfit', sans-serif;
      font-size: 19px;
      font-weight: 700;
      letter-spacing: -0.02em;
      color: var(--ink);
      margin: 6px 0 8px;
    }
    .feature-card p, .pipeline-card p {
      font-size: 13.5px;
      color: var(--muted);
      line-height: 1.65;
    }
    .pipeline-step-num {
      display: inline-flex;
      background: var(--sage-deep);
      color: #F6F3EB;
      font-family: 'Outfit', sans-serif;
      font-weight: 800;
      font-size: 11.5px;
      letter-spacing: 0.08em;
      border-radius: 999px;
      padding: 4px 12px;
      margin-bottom: 8px;
    }

    /* INPUTS & UPLOAD */
    label.field-label {
      display: block;
      font-size: 13px;
      font-weight: 600;
      color: var(--ink);
      margin-bottom: 6px;
    }
    .text-input, .textarea-input, .select-input {
      width: 100%;
      background: var(--card);
      color: var(--ink);
      border: 1px solid var(--border);
      border-radius: 14px;
      padding: 12px 14px;
      font-family: 'DM Sans', sans-serif;
      font-size: 14px;
      margin-bottom: 14px;
      outline: none;
    }
    .text-input:focus, .textarea-input:focus, .select-input:focus {
      border-color: var(--sage-deep);
      box-shadow: 0 0 0 3px rgba(74, 85, 54, 0.16);
    }
    .drop-zone {
      background: var(--bg-soft);
      border: 2px dashed #9CA58E;
      border-radius: 16px;
      padding: 34px 16px;
      text-align: center;
      cursor: pointer;
      transition: all 0.2s ease;
    }
    .drop-zone:hover, .drop-zone.dragover {
      background: #EFF2E8;
      border-color: var(--sage-deep);
    }

    /* TABS, TAGS, ALERTS & METRICS */
    .tabs-bar {
      display: flex;
      gap: 8px;
      border-bottom: 1px solid var(--border);
      padding-bottom: 10px;
      margin-bottom: 18px;
    }
    .tab-pill {
      background: transparent;
      border: none;
      font-family: 'Outfit', sans-serif;
      font-weight: 700;
      font-size: 14px;
      color: var(--muted);
      padding: 6px 14px;
      border-radius: 999px;
      cursor: pointer;
    }
    .tab-pill.active {
      background: var(--sage-tint);
      color: var(--sage-deep);
    }
    .alert {
      border-radius: 14px;
      padding: 12px 16px;
      font-size: 13.5px;
      margin-bottom: 16px;
      line-height: 1.55;
    }
    .alert-info { background: #EFF2E8; color: #364125; border: 1px solid #C8D2B7; }
    .alert-success { background: #E7EFE0; color: #2E4722; border: 1px solid #BFD1B0; }
    .alert-error { background: #F8E8E4; color: #7E3024; border: 1px solid #E3BEB4; }

    .skill-tag {
      display: inline-block;
      background: var(--sage-tint);
      color: #374325;
      border: 1px solid #C5CEB4;
      border-radius: 999px;
      padding: 5px 13px;
      margin: 4px;
      font-size: 12px;
      font-weight: 600;
    }
    .missing-tag {
      display: inline-block;
      background: var(--terracotta-bg);
      color: #7E3B2E;
      border: 1px solid #DFC0B6;
      border-radius: 999px;
      padding: 5px 13px;
      margin: 4px;
      font-size: 12px;
      font-weight: 600;
    }
    .metric-card {
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 20px;
      padding: 18px 20px;
    }
    .metric-label {
      color: var(--muted);
      font-size: 11px;
      font-weight: 700;
      letter-spacing: 0.1em;
      text-transform: uppercase;
    }
    .metric-val {
      font-family: 'Outfit', sans-serif;
      font-weight: 800;
      font-size: 28px;
      color: var(--ink);
      margin-top: 4px;
    }

    /* DARK OLIVE FOOTER */
    .footer {
      background: linear-gradient(135deg, #2D3622 0%, #202818 100%);
      border: 1px solid #445234;
      color: #C9D0BF;
      border-radius: 16px;
      padding: 14px 24px;
      margin-top: 40px;
      font-size: 12.5px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 10px;
      box-shadow: 0 8px 20px rgba(32, 40, 24, 0.14);
    }
    .footer .brand { font-size: 16px; color: #F6F3EB; cursor: default; }
    .footer .brand-badge { width: 26px; height: 26px; font-size: 14px; border-radius: 8px; background: #A7B099; color: #202818; }
    .footer .brand-accent { color: #BCC6AC; }
    .footer-meta { color: #B8C1AC; font-size: 12px; }

    .view { display: none; }
    .view.active { display: block; }
    .hidden { display: none !important; }
    .divider { border: 0; border-top: 1px solid var(--border); margin: 26px 0; }
    table.neural-table { width: 100%; border-collapse: collapse; font-size: 13.5px; }
    table.neural-table th, table.neural-table td {
      padding: 10px 12px;
      text-align: left;
      border-bottom: 1px solid var(--border);
    }
    table.neural-table th {
      font-family: 'Outfit', sans-serif;
      font-size: 11.5px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: var(--muted);
    }
    .espresso-band {
      background: var(--espresso-dark);
      color: #EDEAE2;
      border-radius: 24px;
      padding: 26px 30px;
      margin: 22px 0;
    }
    .progress-track {
      height: 10px;
      background: #DCD4C6;
      border-radius: 999px;
      overflow: hidden;
      margin: 10px 0 16px;
    }
    .progress-fill {
      height: 100%;
      background: var(--sage-deep);
      border-radius: 999px;
      transition: width 0.3s ease;
    }
  </style>
</head>
<body>
<div class="page-shell">
  <!-- HEADER -->
  <header class="topbar">
    <div class="brand" onclick="navigateTo('Home')">
      <span class="brand-badge">R</span>RESUMIND <span class="brand-accent">AI</span>
    </div>
    <nav class="nav-dock">
      <button class="nav-btn active" id="navHome" onclick="navigateTo('Home')">HOME</button>
      <button class="nav-btn" id="navAnalysis" onclick="navigateProtected('Analysis')">ANALYSER</button>
      <button class="nav-btn" id="navCareerPaths" onclick="navigateProtected('CareerPaths')">CAREER PATHS 🧭</button>
      <button class="nav-btn" id="navInterview" onclick="navigateProtected('Interview')">MOCK INTERVIEW 🎯</button>
      <button class="nav-btn" id="navAuth" onclick="openAuthOrAccount()">SIGN IN</button>
    </nav>
  </header>

  <!-- VIEW: HOME -->
  <section id="viewHome" class="view active">
    <div class="hero scroll-pop">
      <span class="hero-tag">✦ RESUMIND AI ENGINE</span>
      <h1>A sharper resume.<br><em>Your next defining role.</em></h1>
      <p>Analyse your professional experience, discover your strengths and understand how your qualifications align with your next career opportunity. Supporting IT and non-IT resume analysis.</p>
    </div>

    <div style="text-align:center; margin: 18px 0 28px;">
      <button class="btn-primary" style="min-width: 280px;" onclick="navigateProtected('Analysis')">ANALYSE MY RESUME →</button>
    </div>

    <div class="scroll-pop" style="display:flex; justify-content:space-between; align-items:flex-end; flex-wrap:wrap; gap:16px; margin: 26px 0 18px;">
      <div>
        <span class="section-tag">CAPABILITIES COLLECTION</span>
        <div class="section-heading" style="margin:6px 0 0;">Simplifying career<br>intelligence with clarity</div>
      </div>
      <p style="max-width:450px; color:var(--muted); font-size:14px; margin:0;">
        We evaluate more than keywords. Resumind AI parses your full PDF layout, runs custom PyTorch neural networks, audits ATS compatibility, and maps your clearest next career step.
      </p>
    </div>

    <div class="grid-3">
      <div class="card feature-card scroll-pop">
        <span class="section-tag">MODULE 01</span>
        <h3>Resume Observation</h3>
        <p>Layout-aware PDF extraction captures contact details, summaries, education, employment timelines, projects, certifications, and languages.</p>
      </div>
      <div class="card feature-card scroll-pop scroll-pop-delay-1">
        <span class="section-tag">MODULE 02</span>
        <h3>Industry Recognition</h3>
        <p>Scans across 14 IT, non-IT, and hybrid professional domains—from Software &amp; AI to Finance, Marketing, HR, Healthcare, and Operations.</p>
      </div>
      <div class="card feature-card scroll-pop scroll-pop-delay-2">
        <span class="section-tag">MODULE 03</span>
        <h3>Job Compatibility</h3>
        <p>Benchmarks your detected competencies against any target job description to surface matched skills, critical gaps, and overlap percentages.</p>
      </div>
      <div class="card feature-card scroll-pop">
        <span class="section-tag">MODULE 04</span>
        <h3>Neural SkillNet &amp; MatchNet</h3>
        <p>Dual custom PyTorch neural models predict verified skill confidence and semantic resume-to-job compatibility scores.</p>
      </div>
      <div class="card feature-card scroll-pop scroll-pop-delay-1">
        <span class="section-tag">MODULE 05</span>
        <h3>Resume Diagnostics</h3>
        <p>Highlights missing resume sections, ATS parseability checks, quantified achievement opportunities, and tailored improvement suggestions.</p>
      </div>
      <div class="card feature-card scroll-pop scroll-pop-delay-2">
        <span class="section-tag">MODULE 06</span>
        <h3>Executive Reporting</h3>
        <p>Generates downloadable ReportLab PDF career audit reports plus role recommendations and skill-calibrated mock interviews.</p>
      </div>
    </div>

    <div class="scroll-pop" style="margin: 34px 0 16px;">
      <span class="section-tag">INSIDE THE RESUME AUDIT</span>
      <div class="section-heading">How Resumind Analyses Your Resume</div>
      <p style="max-width:660px; color:var(--muted); font-size:14px;">Every uploaded resume passes through a structured four-stage intelligence pipeline designed for precision, readability, and actionable career guidance.</p>
    </div>

    <div class="grid-2">
      <div class="card pipeline-card scroll-pop">
        <span class="pipeline-step-num">STAGE 01 • PARSE</span>
        <h4>Structured PDF &amp; Section Decoding</h4>
        <p>PyMuPDF reads multi-column and single-column resumes in logical reading order, isolating headings, dates, qualifications, projects, and contact links.</p>
      </div>
      <div class="card pipeline-card scroll-pop scroll-pop-delay-1">
        <span class="pipeline-step-num">STAGE 02 • CLASSIFY</span>
        <h4>PyTorch Neural Skill Inference</h4>
        <p>Resumind SkillNet evaluates TF-IDF n-gram signals alongside our curated skill dictionary to assign confidence scores to every recognized competency.</p>
      </div>
      <div class="card pipeline-card scroll-pop">
        <span class="pipeline-step-num">STAGE 03 • AUDIT</span>
        <h4>ATS Calibration &amp; Gap Detection</h4>
        <p>ResumindMatchNet and our deterministic matcher blend semantic similarity with exact requirement overlap to calculate suitability scores and pinpoint missing target skills.</p>
      </div>
      <div class="card pipeline-card scroll-pop scroll-pop-delay-1">
        <span class="pipeline-step-num">STAGE 04 • LAUNCH</span>
        <h4>Career Radar &amp; Mock Interview Prep</h4>
        <p>Automatically ranks your highest-fit job roles with direct apply links, builds customized MCQ mock interviews from your resume skills, and exports a clean PDF audit.</p>
      </div>
    </div>
  </section>

  <!-- VIEW: LOGIN / SIGN UP -->
  <section id="viewLogin" class="view">
    <div class="hero">
      <span class="hero-tag">✦ SUPABASE AUTHENTICATION</span>
      <h1>Welcome to<br><em>Resumind AI</em></h1>
      <p>Sign in or create your account to unlock the neural Resume Analyser, Career Paths, Mock Interview Studio, and cloud-saved audit history.</p>
    </div>

    <div id="loginRedirectBanner" class="alert alert-info hidden"></div>

    <div style="max-width: 540px; margin: 0 auto;" class="card">
      <div class="tabs-bar">
        <button class="tab-pill active" id="tabBtnSignIn" onclick="switchAuthTab('signin')">Sign In</button>
        <button class="tab-pill" id="tabBtnSignUp" onclick="switchAuthTab('signup')">Create Account</button>
        <button class="tab-pill" id="tabBtnReset" onclick="switchAuthTab('reset')">Reset Password</button>
      </div>
      <div id="authMsg" class="alert hidden"></div>

      <form id="formSignIn" onsubmit="handleSignIn(event)">
        <span class="panel-badge">MEMBER ACCESS</span>
        <h3 style="font-family:'Outfit',sans-serif; margin-bottom:12px;">Sign in to your account</h3>
        <label class="field-label">Email Address</label>
        <input type="email" id="loginEmail" class="text-input" placeholder="you@example.com" required>
        <label class="field-label">Password</label>
        <input type="password" id="loginPassword" class="text-input" placeholder="Enter your password" required>
        <button type="submit" class="btn-primary" style="width:100%;" id="btnSignIn">SIGN IN →</button>
      </form>

      <form id="formSignUp" class="hidden" onsubmit="handleSignUp(event)">
        <span class="panel-badge">NEW ACCOUNT</span>
        <h3 style="font-family:'Outfit',sans-serif; margin-bottom:12px;">Create your Resumind AI account</h3>
        <label class="field-label">Full Name</label>
        <input type="text" id="regName" class="text-input" placeholder="Jane Doe" required>
        <label class="field-label">Email Address</label>
        <input type="email" id="regEmail" class="text-input" placeholder="you@example.com" required>
        <label class="field-label">Password (min 6 characters)</label>
        <input type="password" id="regPassword" class="text-input" placeholder="Create a strong password" required minlength="6">
        <label class="field-label">Confirm Password</label>
        <input type="password" id="regConfirm" class="text-input" placeholder="Re-enter password" required minlength="6">
        <button type="submit" class="btn-primary" style="width:100%;" id="btnSignUp">CREATE ACCOUNT →</button>
      </form>

      <form id="formReset" class="hidden" onsubmit="handleReset(event)">
        <span class="panel-badge">ACCOUNT RECOVERY</span>
        <h3 style="font-family:'Outfit',sans-serif; margin-bottom:12px;">Reset your password</h3>
        <label class="field-label">Registered Email</label>
        <input type="email" id="resetEmail" class="text-input" placeholder="you@example.com" required>
        <button type="submit" class="btn-secondary" style="width:100%;">SEND PASSWORD RESET LINK</button>
      </form>
    </div>
  </section>

  <!-- VIEW: ACCOUNT & SAVED HISTORY -->
  <section id="viewAccount" class="view">
    <div class="hero">
      <span class="hero-tag">✦ MEMBER WORKSPACE</span>
      <h1 id="accountNameHeading">Member</h1>
      <p id="accountEmailSub">Synced with Supabase</p>
    </div>

    <div class="grid-3" style="margin-bottom: 24px;">
      <button class="btn-primary" onclick="navigateTo('Analysis')">ANALYSE NEW RESUME →</button>
      <button class="btn-secondary" onclick="navigateTo('Interview')">TAKE MOCK INTERVIEW 🎯</button>
      <button class="btn-secondary" onclick="handleSignOut()">SIGN OUT</button>
    </div>

    <hr class="divider">
    <span class="section-tag">SUPABASE DATABASE</span>
    <div class="section-heading">Saved Resume Analyses</div>
    <div id="savedAnalysesList"></div>

    <hr class="divider">
    <span class="section-tag">ASSESSMENT RECORDS</span>
    <div class="section-heading">Mock Interview History</div>
    <div id="savedInterviewsList"></div>
  </section>

  <!-- VIEW: ANALYSER -->
  <section id="viewAnalysis" class="view">
    <div class="hero">
      <span class="hero-tag">RESUME EVALUATION STUDIO</span>
      <h1>Resume Analysis<br><em>Studio</em></h1>
      <p>Upload your PDF resume. Resumind AI will inspect your professional background, identify skills and organise your career information.</p>
    </div>

    <div class="grid-2" style="margin-bottom: 18px;">
      <div class="card">
        <span class="panel-badge">STEP 1</span>
        <h4 style="font-family:'Outfit',sans-serif; font-size:19px; margin-bottom:4px;">Upload PDF Resume</h4>
        <p style="font-size:13px; color:var(--muted); margin-bottom:12px;">Select or drop your text-based PDF resume (supports IT &amp; non-IT).</p>
        <div class="drop-zone" id="dropZone" onclick="document.getElementById('fileInput').click()">
          <div style="font-weight:700; font-size:15px; margin-bottom:4px;">Click or drag PDF resume here</div>
          <div style="font-size:12.5px; color:var(--muted);">Accepted format: Adobe PDF (.pdf)</div>
          <input type="file" id="fileInput" class="hidden" accept=".pdf" onchange="handleFileSelected(this.files[0])">
          <div id="fileInfo" style="margin-top:12px; font-weight:700; color:var(--sage-deep); font-size:13px;"></div>
        </div>
      </div>

      <div class="card">
        <span class="panel-badge">STEP 2</span>
        <h4 style="font-family:'Outfit',sans-serif; font-size:19px; margin-bottom:4px;">Target Job Description <span style="font-weight:400; color:var(--muted); font-size:12px;">(Optional)</span></h4>
        <p style="font-size:13px; color:var(--muted); margin-bottom:12px;">Paste job requirements to run ATS skill matching and gap analysis.</p>
        <textarea id="jdInput" class="textarea-input" style="min-height:142px; margin-bottom:0;" placeholder="Paste the job description here if you want a resume-to-job comparison, ATS score & keyword match..."></textarea>
      </div>
    </div>

    <button class="btn-primary" id="btnAnalyse" style="width:100%;" onclick="runResumeAnalysis()">ANALYSE RESUME →</button>
    <div id="analysisStatus" class="alert hidden" style="margin-top:16px;"></div>

    <div id="analysisDashboard" class="hidden">
      <hr class="divider">
      <span class="section-tag">CAREER AUDIT</span>
      <div class="section-heading">Candidate Profile</div>
      <div class="grid-3" style="margin-bottom:12px;">
        <div class="metric-card"><div class="metric-label">Candidate</div><div class="metric-val" id="resCandName">--</div></div>
        <div class="metric-card"><div class="metric-label">Email</div><div class="metric-val" style="font-size:18px;" id="resCandEmail">--</div></div>
        <div class="metric-card"><div class="metric-label">Phone</div><div class="metric-val" style="font-size:20px;" id="resCandPhone">--</div></div>
      </div>
      <p id="resMetaLine" style="font-size:13px; color:var(--muted); margin-bottom:8px;"></p>

      <hr class="divider">
      <span class="section-tag">AI CAREER RADAR</span>
      <div class="section-heading">Top Predicted Job Roles &amp; Career Paths</div>
      <div id="resCareerRadar"></div>

      <hr class="divider">
      <span class="section-tag">JOB COMPATIBILITY</span>
      <div class="section-heading">Skills Match Analysis</div>
      <div id="resMatchSection"></div>

      <hr class="divider">
      <span class="section-tag">COMPETENCY TAXONOMY</span>
      <div class="section-heading">Detected Skills</div>
      <div id="resDetectedSkills"></div>

      <hr class="divider">
      <span class="section-tag">EXECUTIVE INTELLIGENCE</span>
      <div class="section-heading">Complete Resumind AI Analysis</div>
      <div class="card" id="resAiReport" style="white-space:pre-wrap; font-size:14px; line-height:1.7;"></div>

      <div id="resNeuralWrap" class="hidden">
        <hr class="divider">
        <h3 style="font-family:'Outfit',sans-serif; margin-bottom:10px;">✦ Resumind Neural Network Predictions (PyTorch SkillNet)</h3>
        <div class="card" style="overflow-x:auto;">
          <table class="neural-table" id="resNeuralTable"></table>
        </div>
      </div>

      <div class="espresso-band">
        <span class="panel-badge" style="background:#A7B099; color:#202818; border:none;">✦ NEXT STEP: INTERVIEW PREPARATION</span>
        <h3 style="font-family:'Outfit',sans-serif; font-size:22px; color:#F7F4EC; margin:6px 0;">Test Your Knowledge with an AI Mock Interview</h3>
        <p style="font-size:14px; color:#D5CCC2; margin-bottom:14px;">Take an interactive test calibrated directly to your resume's detected skills and career category.</p>
        <button class="btn-primary" style="background:#A7B099; color:#202818;" onclick="startInterviewFromResume()">START MOCK INTERVIEW TEST BASED ON THIS RESUME →</button>
      </div>

      <div class="grid-2" style="margin-top:18px;">
        <button class="btn-primary" onclick="downloadResumePdf()">DOWNLOAD PDF REPORT</button>
        <button class="btn-secondary" onclick="resetAnalysisView()">START NEW RESUME ANALYSIS</button>
      </div>
    </div>
  </section>

  <!-- VIEW: CAREER PATHS -->
  <section id="viewCareerPaths" class="view">
    <div class="hero">
      <span class="hero-tag">✦ AI CAREER ROADMAP &amp; ROLE PREDICTOR</span>
      <h1>Explore Suitable Job Roles<br><em>&amp; Career Paths</em></h1>
      <p>Discover roles precisely matched to your background, understand why each path fits your profile, identify target skills to learn, and apply directly with one click.</p>
    </div>
    <div id="careerNotice" class="alert alert-info"></div>
    <div id="careerFilterBar" style="display:flex; flex-wrap:wrap; gap:8px; margin-bottom:18px;"></div>
    <div id="careerList"></div>
  </section>

  <!-- VIEW: MOCK INTERVIEW -->
  <section id="viewInterview" class="view">
    <div class="hero">
      <span class="hero-tag">✦ AI INTERVIEW PREPARATION STUDIO</span>
      <h1>Interactive Mock Interview<br><em>&amp; Skill Test</em></h1>
      <p>Test your competencies with questions tailored directly to your skills and domain. Get immediate evaluation, interview readiness grades, and detailed interviewer insights.</p>
    </div>

    <div id="interviewConfigBox" class="card">
      <span class="panel-badge">TEST CONFIGURATION</span>
      <h3 style="font-family:'Outfit',sans-serif; margin-bottom:6px;">Configure Your Mock Interview</h3>
      <div id="interviewSyncNote" class="alert alert-info" style="margin-top:10px;"></div>
      <div class="grid-2">
        <div>
          <label class="field-label">Interview Focus Area</label>
          <select id="intFocusMode" class="select-input">
            <option value="Balanced Mock Interview">Balanced Mock Interview</option>
            <option value="Technical Only">Technical Only</option>
            <option value="Behavioral & Leadership">Behavioral &amp; Leadership</option>
          </select>
        </div>
        <div>
          <label class="field-label">Number of Questions</label>
          <select id="intNumQ" class="select-input">
            <option value="3">3 Questions</option>
            <option value="5" selected>5 Questions</option>
            <option value="8">8 Questions</option>
            <option value="10">10 Questions</option>
            <option value="15">15 Questions</option>
          </select>
        </div>
      </div>
      <label class="field-label">Target Skills (comma-separated)</label>
      <input type="text" id="intSkillsInput" class="text-input" value="Python, SQL, Git, Problem Solving">
      <button class="btn-primary" style="width:100%;" onclick="generateMockInterview()">GENERATE &amp; START TEST →</button>
    </div>

    <div id="interviewQuizBox" class="hidden">
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
        <div class="section-heading" style="margin:0; font-size:24px;" id="quizHeader">Assessment In Progress</div>
        <button class="btn-secondary" onclick="resetInterviewState()">RESET TEST ✕</button>
      </div>
      <div class="progress-track"><div class="progress-fill" id="quizProgressFill" style="width:0%;"></div></div>
      <div id="quizQuestionsList"></div>
      <button class="btn-primary" style="width:100%; margin-top:12px;" onclick="submitMockInterview()">SUBMIT TEST &amp; VIEW EVALUATION →</button>
    </div>

    <div id="interviewResultBox" class="hidden"></div>
  </section>

  <!-- FOOTER -->
  <footer class="footer scroll-pop">
    <div class="brand"><span class="brand-badge">R</span>RESUMIND <span class="brand-accent">AI</span></div>
    <div class="footer-meta">Your Resume. Your Skills. Your Next Opportunity. &bull; &copy; 2026 Resumind AI</div>
  </footer>
</div>

<script>
  const state = {
    view: 'Home',
    pendingView: null,
    auth: JSON.parse(localStorage.getItem('resumind_auth') || 'null'),
    selectedFile: null,
    analysisResult: null,
    careerData: null,
    careerCategory: 'All Domains',
    interviewQuestions: null,
    interviewAnswers: {},
    interviewEval: null,
    interviewFocusMode: 'Balanced Mock Interview',
  };

  function authHeaders(extra = {}) {
    const h = { ...extra };
    if (state.auth && state.auth.access_token) {
      h['Authorization'] = 'Bearer ' + state.auth.access_token;
      h['X-Refresh-Token'] = state.auth.refresh_token || '';
    }
    return h;
  }

  function escapeHtml(str) {
    return String(str ?? '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function updateNav() {
    document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
    const map = { Home: 'navHome', Analysis: 'navAnalysis', CareerPaths: 'navCareerPaths', Interview: 'navInterview', Login: 'navAuth', Account: 'navAuth' };
    const activeBtn = document.getElementById(map[state.view]);
    if (activeBtn) activeBtn.classList.add('active');
    const authBtn = document.getElementById('navAuth');
    authBtn.textContent = state.auth ? 'ACCOUNT 👤' : 'SIGN IN';
  }

  function navigateTo(view) {
    state.view = view;
    document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
    document.getElementById('view' + view).classList.add('active');
    updateNav();
    window.scrollTo({ top: 0, behavior: 'smooth' });
    setTimeout(updateScrollPop, 60);
    if (view === 'Account') loadAccountHistory();
    if (view === 'CareerPaths') loadCareerPaths();
    if (view === 'Interview') syncInterviewConfig();
  }

  function navigateProtected(targetView) {
    if (state.auth && state.auth.access_token) {
      navigateTo(targetView);
    } else {
      state.pendingView = targetView;
      const labels = { Analysis: 'Resume Analyser', CareerPaths: 'Career Paths', Interview: 'Mock Interview Studio' };
      const banner = document.getElementById('loginRedirectBanner');
      banner.innerHTML = '🔒 Please sign in or create an account to continue to <b>' + escapeHtml(labels[targetView] || 'the studio') + '</b>.';
      banner.classList.remove('hidden');
      navigateTo('Login');
    }
  }

  function openAuthOrAccount() {
    if (state.auth && state.auth.access_token) {
      navigateTo('Account');
    } else {
      document.getElementById('loginRedirectBanner').classList.add('hidden');
      navigateTo('Login');
    }
  }

  function switchAuthTab(tab) {
    ['signin', 'signup', 'reset'].forEach(t => {
      document.getElementById('tabBtn' + (t === 'signin' ? 'SignIn' : t === 'signup' ? 'SignUp' : 'Reset')).classList.toggle('active', t === tab);
      document.getElementById('form' + (t === 'signin' ? 'SignIn' : t === 'signup' ? 'SignUp' : 'Reset')).classList.toggle('hidden', t !== tab);
    });
    document.getElementById('authMsg').classList.add('hidden');
  }

  function showAuthMsg(msg, isSuccess = false) {
    const box = document.getElementById('authMsg');
    box.className = 'alert ' + (isSuccess ? 'alert-success' : 'alert-error');
    box.textContent = msg;
    box.classList.remove('hidden');
  }

  async function handleSignIn(e) {
    e.preventDefault();
    const btn = document.getElementById('btnSignIn');
    btn.disabled = true;
    try {
      const res = await fetch('/api/auth/signin', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: document.getElementById('loginEmail').value.trim(),
          password: document.getElementById('loginPassword').value,
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Sign-in failed.');
      state.auth = { user: data.user, access_token: data.access_token, refresh_token: data.refresh_token };
      localStorage.setItem('resumind_auth', JSON.stringify(state.auth));
      const next = state.pendingView || 'Analysis';
      state.pendingView = null;
      navigateTo(next);
    } catch (err) {
      showAuthMsg(err.message);
    } finally {
      btn.disabled = false;
    }
  }

  async function handleSignUp(e) {
    e.preventDefault();
    const pw = document.getElementById('regPassword').value;
    const pw2 = document.getElementById('regConfirm').value;
    if (pw !== pw2) return showAuthMsg('Passwords do not match.');
    const btn = document.getElementById('btnSignUp');
    btn.disabled = true;
    try {
      const res = await fetch('/api/auth/signup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          full_name: document.getElementById('regName').value.trim(),
          email: document.getElementById('regEmail').value.trim(),
          password: pw,
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Sign-up failed.');
      if (data.needs_email_confirmation) {
        showAuthMsg('Account created! Please confirm your email inbox link, then sign in.', true);
      } else {
        state.auth = { user: data.user, access_token: data.access_token, refresh_token: data.refresh_token };
        localStorage.setItem('resumind_auth', JSON.stringify(state.auth));
        const next = state.pendingView || 'Analysis';
        state.pendingView = null;
        navigateTo(next);
      }
    } catch (err) {
      showAuthMsg(err.message);
    } finally {
      btn.disabled = false;
    }
  }

  async function handleReset(e) {
    e.preventDefault();
    try {
      const res = await fetch('/api/auth/reset-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: document.getElementById('resetEmail').value.trim() }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Reset failed.');
      showAuthMsg('If an account exists for that email, a password reset link has been sent.', true);
    } catch (err) {
      showAuthMsg(err.message);
    }
  }

  async function handleSignOut() {
    try { await fetch('/api/auth/signout', { method: 'POST', headers: authHeaders() }); } catch (_) {}
    state.auth = null;
    state.analysisResult = null;
    localStorage.removeItem('resumind_auth');
    navigateTo('Home');
  }

  async function loadAccountHistory() {
    if (!state.auth) return navigateTo('Login');
    document.getElementById('accountNameHeading').textContent = state.auth.user.full_name || 'Member';
    document.getElementById('accountEmailSub').textContent = (state.auth.user.email || '') + ' • Synced with Supabase';
    const aList = document.getElementById('savedAnalysesList');
    const iList = document.getElementById('savedInterviewsList');
    aList.innerHTML = '<div class="alert alert-info">Loading saved analyses...</div>';
    iList.innerHTML = '<div class="alert alert-info">Loading interview history...</div>';
    try {
      const res = await fetch('/api/account/history', { headers: authHeaders() });
      if (res.status === 401) { handleSignOut(); return; }
      const data = await res.json();
      document.getElementById('accountNameHeading').textContent = data.user.full_name || 'Member';
      if (!data.analyses || !data.analyses.length) {
        aList.innerHTML = '<div class="alert alert-info">No saved resume analyses yet.</div>';
      } else {
        aList.innerHTML = data.analyses.map(row => `
          <div class="card" style="margin-bottom:12px; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px;">
            <div>
              <span class="panel-badge">${escapeHtml(row.career_category || 'AUDIT')}</span>
              <span class="skill-tag">${row.match_score !== null ? escapeHtml(row.match_score) + '%' : 'General Audit'}</span>
              <h4 style="font-family:'Outfit',sans-serif; margin-top:6px;">${escapeHtml(row.file_name)}</h4>
              <p style="font-size:13px; color:var(--muted);">Candidate: <b>${escapeHtml(row.candidate_name)}</b> • ${escapeHtml((row.created_at || '').slice(0, 19).replace('T', ' '))}</p>
            </div>
            <div style="display:flex; gap:8px;">
              <button class="btn-primary" style="padding:9px 18px;" onclick='openSavedAudit(${JSON.stringify(row).replace(/'/g, "&#39;")})'>Open Audit</button>
              <button class="btn-secondary" style="padding:9px 16px;" onclick="deleteSavedAudit('${escapeHtml(row.id)}')">Delete</button>
            </div>
          </div>
        `).join('');
      }

      if (!data.interviews || !data.interviews.length) {
        iList.innerHTML = '<div class="alert alert-info">No mock interview attempts saved yet.</div>';
      } else {
        iList.innerHTML = data.interviews.map(item => `
          <div class="card" style="margin-bottom:12px; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px;">
            <div>
              <span class="panel-badge">${escapeHtml(item.readiness_tier)}</span>
              <span class="skill-tag">${escapeHtml(item.focus_mode)}</span>
              <div style="font-family:'Outfit',sans-serif; font-weight:700; font-size:17px; margin-top:6px;">Score: ${escapeHtml(item.score_pct)}% (${escapeHtml(item.correct_count)}/${escapeHtml(item.total_questions)})</div>
              <div style="font-size:12.5px; color:var(--muted);">Revision: ${escapeHtml((item.weak_skills || []).join(', ') || 'Strong across all tested skills')}</div>
            </div>
            <div style="font-size:12px; color:var(--muted);">${escapeHtml((item.created_at || '').slice(0, 19).replace('T', ' '))}</div>
          </div>
        `).join('');
      }
    } catch (err) {
      aList.innerHTML = '<div class="alert alert-error">Could not load account history.</div>';
    }
  }

  function openSavedAudit(row) {
    const detected = row.detected_skills || {};
    const allSkills = Object.values(detected).flat();
    const matched = row.matched_skills || [];
    const missing = row.missing_skills || [];
    state.analysisResult = {
      saved_id: row.id,
      filename: row.file_name,
      created_at: (row.created_at || '').slice(0, 19).replace('T', ' '),
      candidate: { name: row.candidate_name || 'Candidate', email: row.candidate_email || 'Not found', phone: 'Not found' },
      soura_result: {
        engine: 'Resumind Custom PyTorch AI',
        resume_category: row.career_category || 'Technical Professional',
        skills: detected,
        trained_skill_predictions: row.neural_predictions || [],
        trained_model_status: 'Loaded from Supabase History',
        ai_analysis: row.ai_analysis || '',
      },
      match_data: {
        resume_skills: allSkills,
        required_skills: [...new Set([...matched, ...missing])],
        matched_skills: matched,
        missing_skills: missing,
        match_score: row.match_score,
      },
      predicted_roles: [],
    };
    navigateTo('Analysis');
    renderAnalysisDashboard(state.analysisResult);
  }

  async function deleteSavedAudit(id) {
    await fetch('/api/account/analyses/' + encodeURIComponent(id), { method: 'DELETE', headers: authHeaders() });
    loadAccountHistory();
  }

  // FILE DROP & ANALYSIS
  const dropZone = document.getElementById('dropZone');
  ['dragenter', 'dragover'].forEach(ev => dropZone.addEventListener(ev, e => { e.preventDefault(); dropZone.classList.add('dragover'); }));
  ['dragleave', 'drop'].forEach(ev => dropZone.addEventListener(ev, e => { e.preventDefault(); dropZone.classList.remove('dragover'); }));
  dropZone.addEventListener('drop', e => {
    const f = e.dataTransfer.files[0];
    if (f && f.name.toLowerCase().endsWith('.pdf')) handleFileSelected(f);
  });

  function handleFileSelected(file) {
    if (!file) return;
    state.selectedFile = file;
    document.getElementById('fileInfo').textContent = `✓ Resume loaded: ${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
  }

  async function runResumeAnalysis() {
    if (!state.selectedFile) return alert('Please upload a PDF resume first.');
    const btn = document.getElementById('btnAnalyse');
    const status = document.getElementById('analysisStatus');
    btn.disabled = true;
    status.className = 'alert alert-info';
    status.textContent = 'Resumind AI is analysing your resume with custom PyTorch models...';
    status.classList.remove('hidden');

    const fd = new FormData();
    fd.append('file', state.selectedFile);
    fd.append('job_description', document.getElementById('jdInput').value.trim());

    try {
      const res = await fetch('/api/analyze', { method: 'POST', headers: authHeaders(), body: fd });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Analysis failed.');
      state.analysisResult = data;
      status.className = 'alert alert-success';
      status.textContent = data.saved_id
        ? '✓ Resumind AI analysis completed and saved to your Supabase account!'
        : '✓ Resumind AI analysis completed!';
      renderAnalysisDashboard(data);
    } catch (err) {
      status.className = 'alert alert-error';
      status.textContent = 'Analysis failed: ' + err.message;
    } finally {
      btn.disabled = false;
    }
  }

  function renderRoleCard(role, idx, showFit = true) {
    const matchedTags = (role.matched_skills || []).map(s => `<span class="skill-tag">✓ ${escapeHtml(s)}</span>`).join('') || '<span style="font-size:12px;color:var(--muted);">Foundational overlap</span>';
    const missingTags = (role.skills_to_learn || []).map(s => `<span class="missing-tag">+ ${escapeHtml(s)}</span>`).join('') || '<span style="font-size:12px;color:var(--muted);">Core requirements satisfied!</span>';
    return `
      <div class="card" style="margin-bottom:16px;">
        <div style="display:flex; justify-content:space-between; align-items:flex-start; gap:12px; flex-wrap:wrap;">
          <div>
            <span class="panel-badge">ROLE #${idx + 1}</span>
            <span class="skill-tag" style="background:#EDEAE2; color:#5A4D43; border-color:#D7D0C1;">${escapeHtml(role.category)}</span>
            <h3 style="font-family:'Outfit',sans-serif; font-size:21px; margin:4px 0;">${escapeHtml(role.title)}</h3>
          </div>
          ${showFit ? `<div style="text-align:right;"><div style="font-family:'Outfit',sans-serif; font-size:28px; font-weight:800; color:${escapeHtml(role.suitability_color)};">${escapeHtml(role.fit_score)}%</div><span class="panel-badge">${escapeHtml(role.suitability_label)}</span></div>` : ''}
        </div>
        <p style="font-size:13.5px; color:var(--muted); margin:6px 0 12px;">${escapeHtml(role.description)}</p>
        ${role.reasoning ? `<div style="background:#F5F2EB; border-left:3px solid ${escapeHtml(role.suitability_color || '#4A5536')}; padding:10px 14px; border-radius:10px; margin-bottom:12px; font-size:13px;"><b>💡 Why this fits:</b> ${escapeHtml(role.reasoning.replace(/\\*\\*/g, ''))}</div>` : ''}
        <div class="grid-2" style="margin-bottom:10px;">
          <div><b style="font-size:13px;">✓ Demonstrated Skills:</b><div>${matchedTags}</div></div>
          <div><b style="font-size:13px;">✦ Skills to Pick Up:</b><div>${missingTags}</div></div>
        </div>
        <div style="font-size:12px; color:var(--muted); border-top:1px solid var(--border); padding-top:8px; margin-bottom:12px;">
          <b>Compensation:</b> ${escapeHtml(role.salary_range)} &nbsp;|&nbsp; <b>Demand:</b> ${escapeHtml(role.market_demand)} &nbsp;|&nbsp; <b>Path:</b> ${escapeHtml(role.growth_path)}
        </div>
        <div style="display:flex; flex-wrap:wrap; gap:8px;">
          <a class="btn-secondary" target="_blank" href="${escapeHtml(role.links.linkedin)}">LinkedIn Jobs ↗</a>
          <a class="btn-secondary" target="_blank" href="${escapeHtml(role.links.indeed)}">Indeed Jobs ↗</a>
          <a class="btn-secondary" target="_blank" href="${escapeHtml(role.links.glassdoor)}">Glassdoor ↗</a>
          <button class="btn-secondary" onclick='launchRoleInterview(${JSON.stringify(role.matched_skills || []).replace(/'/g, "&#39;")}, "${escapeHtml(role.category)}")'>Practice Mock Test 🎯</button>
        </div>
      </div>
    `;
  }

  function renderAnalysisDashboard(data) {
    document.getElementById('analysisDashboard').classList.remove('hidden');
    const c = data.candidate || {};
    const s = data.soura_result || {};
    const m = data.match_data || {};
    document.getElementById('resCandName').textContent = c.name || 'Candidate';
    document.getElementById('resCandEmail').textContent = c.email || 'Not found';
    document.getElementById('resCandPhone').textContent = c.phone || 'Not found';
    document.getElementById('resMetaLine').textContent = `File: ${data.filename || 'resume.pdf'} | Category: ${s.resume_category || 'N/A'} | Engine: ${s.engine || 'PyTorch'} (${s.trained_model_status || 'Active'})`;

    const roles = data.predicted_roles || [];
    document.getElementById('resCareerRadar').innerHTML = roles.map((r, i) => renderRoleCard(r, i, true)).join('') || '<div class="alert alert-info">Open Career Paths to explore matching roles.</div>';

    if (m.match_score !== null && m.match_score !== undefined) {
      document.getElementById('resMatchSection').innerHTML = `
        <div class="grid-3" style="margin-bottom:14px;">
          <div class="metric-card"><div class="metric-label">Skill Overlap</div><div class="metric-val">${escapeHtml(Number(m.match_score).toFixed(1))}%</div></div>
          <div class="metric-card"><div class="metric-label">Matched Skills</div><div class="metric-val">${(m.matched_skills || []).length}</div></div>
          <div class="metric-card"><div class="metric-label">Missing Skills</div><div class="metric-val">${(m.missing_skills || []).length}</div></div>
        </div>
        <div class="grid-2">
          <div class="card"><b>Matched Skills</b><div style="margin-top:8px;">${(m.matched_skills || []).map(x => `<span class="skill-tag">✓ ${escapeHtml(x)}</span>`).join('') || 'None'}</div></div>
          <div class="card"><b>Missing Skills</b><div style="margin-top:8px;">${(m.missing_skills || []).map(x => `<span class="missing-tag">✕ ${escapeHtml(x)}</span>`).join('') || '<span class="skill-tag">All required skills found</span>'}</div></div>
        </div>
      `;
    } else {
      document.getElementById('resMatchSection').innerHTML = '<div class="alert alert-info">💡 No target job description provided — displaying general profile skills and neural SkillNet predictions.</div>';
    }

    const skillsByCat = s.skills || {};
    const catKeys = Object.keys(skillsByCat);
    document.getElementById('resDetectedSkills').innerHTML = catKeys.length
      ? catKeys.map(cat => `<div class="card" style="margin-bottom:12px;"><b>${escapeHtml(cat)}</b><div style="margin-top:6px;">${(skillsByCat[cat] || []).map(sk => `<span class="skill-tag">${escapeHtml(sk)}</span>`).join('')}</div></div>`).join('')
      : '<div class="alert alert-info">No dictionary skills matched.</div>';

    document.getElementById('resAiReport').textContent = s.ai_analysis || '';

    const preds = s.trained_skill_predictions || [];
    if (preds.length) {
      document.getElementById('resNeuralWrap').classList.remove('hidden');
      document.getElementById('resNeuralTable').innerHTML = '<tr><th>Skill</th><th>Confidence</th><th>Predicted</th></tr>' +
        preds.slice(0, 16).map(p => `<tr><td><b>${escapeHtml(p.skill)}</b></td><td>${(Number(p.confidence) * 100).toFixed(1)}%</td><td>${p.predicted_present ? '<span class="skill-tag">YES</span>' : 'NO'}</td></tr>`).join('');
    }
  }

  function resetAnalysisView() {
    state.analysisResult = null;
    state.selectedFile = null;
    document.getElementById('fileInfo').textContent = '';
    document.getElementById('analysisStatus').classList.add('hidden');
    document.getElementById('analysisDashboard').classList.add('hidden');
  }

  async function downloadResumePdf() {
    if (!state.analysisResult) return;
    const res = await fetch('/api/report/resume-pdf', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(state.analysisResult),
    });
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'Resumind_AI_Report.pdf';
    a.click();
    URL.revokeObjectURL(url);
  }

  // CAREER PATHS
  async function loadCareerPaths() {
    const skills = state.analysisResult ? (state.analysisResult.match_data.resume_skills || []) : [];
    const cat = state.analysisResult ? state.analysisResult.soura_result.resume_category : null;
    const notice = document.getElementById('careerNotice');
    notice.innerHTML = skills.length
      ? `🎯 <b>Personalized Career Predictions Active:</b> Based on ${skills.length} detected skills.`
      : '💡 <b>Tip:</b> Upload your resume in <b>ANALYSER</b> for personalized fit scores.';
    const res = await fetch('/api/career-paths', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ candidate_skills: skills, resume_category: cat, top_n: 20 }),
    });
    state.careerData = await res.json();
    renderCareerPaths();
  }

  function setCareerFilter(cat) {
    state.careerCategory = cat;
    renderCareerPaths();
  }

  function renderCareerPaths() {
    if (!state.careerData) return;
    const bar = document.getElementById('careerFilterBar');
    bar.innerHTML = (state.careerData.categories || []).map(cat =>
      `<button class="nav-btn ${state.careerCategory === cat ? 'active' : ''}" onclick="setCareerFilter('${escapeHtml(cat)}')">${escapeHtml(cat)}</button>`
    ).join('');
    const roles = (state.careerData.roles || []).filter(r => state.careerCategory === 'All Domains' || r.category === state.careerCategory);
    document.getElementById('careerList').innerHTML = roles.map((r, i) => renderRoleCard(r, i, state.careerData.personalized)).join('');
  }

  // MOCK INTERVIEW
  function syncInterviewConfig() {
    const note = document.getElementById('interviewSyncNote');
    if (state.analysisResult && (state.analysisResult.match_data.resume_skills || []).length) {
      const sk = state.analysisResult.match_data.resume_skills;
      document.getElementById('intSkillsInput').value = sk.slice(0, 10).join(', ');
      note.innerHTML = `🎯 <b>Resume Synchronized:</b> Testing skills detected in your resume (${escapeHtml(sk.slice(0, 8).join(', '))}).`;
    } else {
      note.innerHTML = '💡 Upload a resume in <b>ANALYSER</b> for automatic skill calibration, or customize your skills below.';
    }
  }

  function launchRoleInterview(skills, category) {
    document.getElementById('intSkillsInput').value = (skills && skills.length ? skills : ['Python', 'SQL', 'Git']).join(', ');
    navigateProtected('Interview');
  }

  function startInterviewFromResume() {
    syncInterviewConfig();
    navigateProtected('Interview');
  }

  async function generateMockInterview() {
    const skills = document.getElementById('intSkillsInput').value.split(',').map(s => s.trim()).filter(Boolean);
    const focusMode = document.getElementById('intFocusMode').value;
    const numQ = Number(document.getElementById('intNumQ').value || 5);
    const cat = state.analysisResult ? state.analysisResult.soura_result.resume_category : 'IT & SOFTWARE';
    state.interviewFocusMode = focusMode;
    const res = await fetch('/api/interview/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ candidate_skills: skills, resume_category: cat, num_questions: numQ, focus_mode: focusMode }),
    });
    const data = await res.json();
    state.interviewQuestions = data.questions || [];
    state.interviewAnswers = {};
    state.interviewEval = null;
    renderQuiz();
  }

  function renderQuiz() {
    document.getElementById('interviewConfigBox').classList.add('hidden');
    document.getElementById('interviewResultBox').classList.add('hidden');
    document.getElementById('interviewQuizBox').classList.remove('hidden');
    const qs = state.interviewQuestions || [];
    document.getElementById('quizHeader').textContent = `Answer the following ${qs.length} questions`;
    document.getElementById('quizQuestionsList').innerHTML = qs.map(q => `
      <div class="card" style="margin-bottom:14px;">
        <div style="display:flex; justify-content:space-between; margin-bottom:8px;">
          <div><span class="panel-badge">QUESTION ${q.question_number} OF ${qs.length}</span> <span class="skill-tag">${escapeHtml(q.skill)}</span></div>
          <span class="panel-badge" style="background:#EDEAE2; color:#5A4D43; border-color:#D7D0C1;">${escapeHtml(q.difficulty)}</span>
        </div>
        <h4 style="font-family:'Outfit',sans-serif; font-size:17px; margin-bottom:12px;">${escapeHtml(q.question)}</h4>
        ${(q.options || []).map((opt, idx) => `
          <label style="display:flex; gap:10px; align-items:flex-start; margin:8px 0; cursor:pointer; font-size:14px;">
            <input type="radio" name="q_${escapeHtml(q.test_id)}" value="${idx}" onchange="recordAnswer('${escapeHtml(q.test_id)}', ${idx})">
            <span>${escapeHtml(opt)}</span>
          </label>
        `).join('')}
      </div>
    `).join('');
    updateQuizProgress();
  }

  function recordAnswer(qId, idx) {
    state.interviewAnswers[qId] = idx;
    updateQuizProgress();
  }

  function updateQuizProgress() {
    const total = (state.interviewQuestions || []).length || 1;
    const answered = Object.keys(state.interviewAnswers).length;
    document.getElementById('quizProgressFill').style.width = `${Math.round((answered / total) * 100)}%`;
  }

  async function submitMockInterview() {
    const qs = state.interviewQuestions || [];
    if (Object.keys(state.interviewAnswers).length < qs.length) {
      return alert(`Please answer all ${qs.length} questions before submitting.`);
    }
    const candName = state.analysisResult ? state.analysisResult.candidate.name : (state.auth ? state.auth.user.full_name : 'Candidate');
    const res = await fetch('/api/interview/evaluate', {
      method: 'POST',
      headers: authHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify({
        questions: qs,
        user_answers: state.interviewAnswers,
        candidate_name: candName,
        focus_mode: state.interviewFocusMode,
        analysis_id: state.analysisResult ? (state.analysisResult.saved_id || null) : null,
      }),
    });
    const data = await res.json();
    state.interviewEval = data.evaluation;
    renderInterviewResults(data.evaluation);
  }

  function renderInterviewResults(ev) {
    document.getElementById('interviewQuizBox').classList.add('hidden');
    const box = document.getElementById('interviewResultBox');
    box.classList.remove('hidden');
    box.innerHTML = `
      <div class="card" style="text-align:center; margin-bottom:20px;">
        <span class="panel-badge">EVALUATION COMPLETE</span>
        <div style="font-family:'Outfit',sans-serif; font-weight:900; font-size:54px; margin:8px 0;">${escapeHtml(ev.score_pct)}%</div>
        <div style="font-weight:700; font-size:17px; color:${escapeHtml(ev.readiness_color)};">${escapeHtml(ev.readiness_badge)}</div>
        <p style="color:var(--muted); font-size:14px; margin-top:6px;">Answered <b>${ev.correct_count}</b> out of <b>${ev.total}</b> questions correctly (${escapeHtml(ev.tier)})</p>
      </div>
      ${(ev.review || []).map(item => {
        const bg = item.is_correct ? '#EBF1E5' : '#F8EAE6';
        const bd = item.is_correct ? '#C3D3B3' : '#E2BEB4';
        return `
          <div class="card" style="background:${bg}; border-color:${bd}; margin-bottom:14px;">
            <div style="font-weight:700; font-size:12px; margin-bottom:6px;">${item.is_correct ? '✓ CORRECT' : '✕ INCORRECT'} • QUESTION ${item.question_number} (${escapeHtml(item.skill)})</div>
            <h4 style="font-family:'Outfit',sans-serif; margin-bottom:8px;">${escapeHtml(item.question)}</h4>
            <p style="font-size:13.5px;"><b>Your Answer:</b> ${escapeHtml(item.user_answer_text)}</p>
            ${!item.is_correct ? `<p style="font-size:13.5px; color:#2E4722;"><b>Correct Answer:</b> ${escapeHtml(item.correct_answer_text)}</p>` : ''}
            <p style="font-size:13px; color:#5A4D43; margin-top:8px;"><b>Explanation:</b> ${escapeHtml(item.explanation)}</p>
            <p style="font-size:13px; color:#4A5536; margin-top:4px;"><b>💡 Interviewer Insight:</b> ${escapeHtml(item.insight)}</p>
          </div>
        `;
      }).join('')}
      <div class="grid-2" style="margin-top:18px;">
        <button class="btn-primary" onclick="downloadInterviewPdf()">DOWNLOAD INTERVIEW REPORT (PDF)</button>
        <button class="btn-secondary" onclick="resetInterviewState()">TAKE A NEW TEST ↻</button>
      </div>
    `;
  }

  async function downloadInterviewPdf() {
    if (!state.interviewEval) return;
    const candName = state.analysisResult ? state.analysisResult.candidate.name : (state.auth ? state.auth.user.full_name : 'Candidate');
    const res = await fetch('/api/report/interview-pdf', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ candidate_name: candName, evaluation_result: state.interviewEval }),
    });
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'Interview_Readiness_Report.pdf';
    a.click();
    URL.revokeObjectURL(url);
  }

  function resetInterviewState() {
    state.interviewQuestions = null;
    state.interviewAnswers = {};
    state.interviewEval = null;
    document.getElementById('interviewQuizBox').classList.add('hidden');
    document.getElementById('interviewResultBox').classList.add('hidden');
    document.getElementById('interviewConfigBox').classList.remove('hidden');
  }

  // BIDIRECTIONAL SCROLL POP-UP ANIMATION
  let scrollTicking = false;
  function updateScrollPop() {
    scrollTicking = false;
    const h = window.innerHeight || document.documentElement.clientHeight || 800;
    document.querySelectorAll('.scroll-pop').forEach(el => {
      const rect = el.getBoundingClientRect();
      if (rect.top < h * 0.92 && rect.bottom > h * 0.06) {
        el.classList.remove('scroll-hidden-bottom', 'scroll-hidden-top');
        el.classList.add('scroll-visible');
      } else if (rect.top >= h - 8) {
        el.classList.remove('scroll-visible', 'scroll-hidden-top');
        el.classList.add('scroll-hidden-bottom');
      } else if (rect.bottom <= 8) {
        el.classList.remove('scroll-visible', 'scroll-hidden-bottom');
        el.classList.add('scroll-hidden-top');
      }
    });
  }
  function onScrollOrResize() {
    if (!scrollTicking) {
      scrollTicking = true;
      window.requestAnimationFrame(updateScrollPop);
    }
  }
  if ('IntersectionObserver' in window) {
    const io = new IntersectionObserver(onScrollOrResize, { root: null, threshold: [0, 0.08, 0.25] });
    document.querySelectorAll('.scroll-pop').forEach(el => io.observe(el));
  }
  window.addEventListener('scroll', onScrollOrResize, { passive: true });
  window.addEventListener('resize', onScrollOrResize, { passive: true });
  updateNav();
  setTimeout(updateScrollPop, 60);
</script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
def index_page():
    return HTMLResponse(content=HTML_CONTENT)
