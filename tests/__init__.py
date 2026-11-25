"""
Resumind AI - Test Suite Package.

This package contains automated tests, verification suites, and benchmarks for:
- Deterministic ATS keyword & taxonomy matching (matcher.py)
- Neural PyTorch inference (ai_engine.inference, SkillNet, ResumindMatchNet)
- Universal resume observer & field extraction (ai_engine.resume_observer)
- Executive resume audit reporting (llm_analyzer.py)
- Mock interview & test generation engine (interview_engine.py)
"""

import sys
from pathlib import Path

# Automatically ensure the project root directory is on sys.path
# so test runners (pytest, unittest, or direct execution)
# can reliably import core application modules without path errors.
PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# =======================================================================
# SHARED TEST FIXTURES & SAMPLES
# =======================================================================

SAMPLE_RESUME_TEXT = """
Jane Doe
Email: jane.doe@example.com | Phone: +1-555-0199
Location: San Francisco, CA | LinkedIn: linkedin.com/in/janedoe

PROFESSIONAL SUMMARY
Senior Full-Stack Software Engineer with 4+ years of experience building
scalable cloud microservices, REST APIs, and modern reactive frontends.

SKILLS
Programming: Python, JavaScript, TypeScript, SQL
Frameworks & Libraries: FastAPI, Django, React, Node.js, PyTorch
Cloud & DevOps: Docker, Kubernetes, AWS (S3, EC2), Git, CI/CD
Databases: PostgreSQL, MongoDB, Redis

EXPERIENCE
Senior Software Engineer | TechCorp (2022 - Present)
- Designed and built microservices using FastAPI, Python, and PostgreSQL.
- Reduced API response latency by 35% through Redis caching and query indexing.
- Led containerized deployments using Docker and Kubernetes on AWS.

EDUCATION
B.Tech in Computer Science & Engineering (2018 - 2022)
"""

SAMPLE_JOB_DESCRIPTION = """
Senior Full-Stack Developer
We are looking for an experienced Senior Full-Stack Developer to lead our backend
and frontend engineering teams.

Key Requirements:
- 3+ years experience with Python and FastAPI or Django.
- Strong proficiency with PostgreSQL, SQL queries, and database optimization.
- Hands-on experience with Docker, containerization, and AWS cloud environments.
- Experience with React, TypeScript, and modern front-end architectures.
- Familiarity with CI/CD workflows and Git version control.
"""

__all__ = [
    "PROJECT_ROOT",
    "SAMPLE_RESUME_TEXT",
    "SAMPLE_JOB_DESCRIPTION",
]
