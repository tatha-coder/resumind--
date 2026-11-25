"""
Resumind AI - Job Prediction & Career Path Recommendation Engine
Analyzes candidate resumes, predicts most suitable job roles,
and generates actionable career paths with detailed justifications and apply links.
100% local and neural-enhanced.
"""

import urllib.parse
from typing import List, Dict, Any, Optional

# =======================================================================
# INDUSTRY JOB ROLES DATABASE (TAXONOMY, PREREQUISITES & MARKET OUTLOOK)
# =======================================================================

JOB_CATALOG: List[Dict[str, Any]] = [
    # ------------------- SOFTWARE & WEB ENGINEERING -------------------
    {
        "id": "fullstack-eng",
        "title": "Full-Stack Software Engineer",
        "category": "IT & SOFTWARE",
        "required_skills": ["Python", "JavaScript", "React", "SQL", "Git", "HTML", "CSS"],
        "bonus_skills": ["TypeScript", "FastAPI", "Docker", "Node.js", "PostgreSQL"],
        "min_experience_years": 1,
        "market_demand": "Very High",
        "salary_range": "$90,000 - $145,000 / ₹10 - 24 LPA",
        "growth_path": "Full-Stack Dev → Lead Engineer → Engineering Manager / Solutions Architect",
        "description": "Designs and delivers end-to-end web applications, encompassing responsive UI client frontends, robust backend REST APIs, and database schemas."
    },
    {
        "id": "backend-python-eng",
        "title": "Backend Engineer (Python / Microservices)",
        "category": "IT & SOFTWARE",
        "required_skills": ["Python", "FastAPI", "Django", "SQL", "Git", "PostgreSQL"],
        "bonus_skills": ["Docker", "Redis", "AWS", "Kubernetes", "Linux"],
        "min_experience_years": 1,
        "market_demand": "High",
        "salary_range": "$95,000 - $150,000 / ₹10 - 26 LPA",
        "growth_path": "Backend Engineer → Senior Distributed Systems Engineer → Principal Architect",
        "description": "Architects high-throughput backend services, asynchronous queues, business logic APIs, and data persistence layers."
    },
    {
        "id": "frontend-react-eng",
        "title": "Frontend Engineer (React / TypeScript)",
        "category": "IT & SOFTWARE",
        "required_skills": ["React", "JavaScript", "TypeScript", "HTML", "CSS", "Git"],
        "bonus_skills": ["Next.js", "Redux", "Tailwind CSS", "Vue", "Node.js"],
        "min_experience_years": 1,
        "market_demand": "High",
        "salary_range": "$85,000 - $135,000 / ₹9 - 22 LPA",
        "growth_path": "Frontend Engineer → Staff Frontend Engineer → Head of UI/UX Engineering",
        "description": "Crafts responsive, accessible, and high-performance interactive user interfaces, client state systems, and web applications."
    },
    {
        "id": "backend-java-eng",
        "title": "Backend Java / Enterprise Engineer",
        "category": "IT & SOFTWARE",
        "required_skills": ["Java", "Spring Boot", "SQL", "Git", "MySQL"],
        "bonus_skills": ["Microservices", "Docker", "Kafka", "AWS", "Kubernetes"],
        "min_experience_years": 1,
        "market_demand": "Very High",
        "salary_range": "$95,000 - $150,000 / ₹10 - 25 LPA",
        "growth_path": "Enterprise Java Dev → Senior Backend Architect → Enterprise Systems Director",
        "description": "Builds resilient enterprise distributed systems, transactional services, and high-volume banking/telecom APIs."
    },
    {
        "id": "systems-cpp-eng",
        "title": "C++ Systems / Low-Latency Engineer",
        "category": "IT & SOFTWARE",
        "required_skills": ["C++", "C", "Linux", "Git", "Data Structures"],
        "bonus_skills": ["Multithreading", "Networking", "TCP/IP", "Docker"],
        "min_experience_years": 1,
        "market_demand": "Moderate (High Premium)",
        "salary_range": "$110,000 - $175,000 / ₹14 - 35 LPA",
        "growth_path": "Systems Engineer → High-Frequency / Infrastructure Architect → Lead Systems Architect",
        "description": "Specializes in performance-critical code, system runtime kernels, gaming engines, and low-latency trading infrastructure."
    },

    # ------------------- DATA SCIENCE & ARTIFICIAL INTELLIGENCE -------------------
    {
        "id": "ml-engineer",
        "title": "Machine Learning Engineer",
        "category": "DATA SCIENCE & AI",
        "required_skills": ["Python", "Machine Learning", "PyTorch", "TensorFlow", "Scikit-learn", "NumPy", "Pandas"],
        "bonus_skills": ["Docker", "Deep Learning", "FastAPI", "SQL", "Computer Vision", "NLP"],
        "min_experience_years": 1,
        "market_demand": "Very High",
        "salary_range": "$110,000 - $170,000 / ₹12 - 30 LPA",
        "growth_path": "ML Engineer → Senior MLOps Engineer → AI Research Director",
        "description": "Bridges research and production by designing, training, evaluating, and deploying neural networks and predictive models at scale."
    },
    {
        "id": "data-scientist",
        "title": "Data Scientist",
        "category": "DATA SCIENCE & AI",
        "required_skills": ["Python", "Data Science", "Statistics", "Machine Learning", "Pandas", "SQL", "Data Analysis"],
        "bonus_skills": ["Data Visualization", "Tableau", "Power BI", "R", "Deep Learning"],
        "min_experience_years": 1,
        "market_demand": "High",
        "salary_range": "$100,000 - $155,000 / ₹11 - 28 LPA",
        "growth_path": "Data Scientist → Lead Scientist → Chief Data Officer (CDO)",
        "description": "Applies statistical modeling, exploratory data mining, and machine learning to uncover business insights and build predictive algorithms."
    },
    {
        "id": "data-analyst",
        "title": "Data Analyst / BI Specialist",
        "category": "DATA SCIENCE & AI",
        "required_skills": ["SQL", "Data Analysis", "Data Visualization", "Power BI", "Tableau", "Excel"],
        "bonus_skills": ["Python", "Pandas", "Statistics", "MySQL"],
        "min_experience_years": 0,
        "market_demand": "Very High",
        "salary_range": "$70,000 - $110,000 / ₹6 - 15 LPA",
        "growth_path": "Data Analyst → Senior Business Intelligence Analyst → Analytics Manager",
        "description": "Translates complex business datasets into intuitive dashboards, KPI trackers, and actionable commercial insights."
    },
    {
        "id": "genai-engineer",
        "title": "Generative AI & LLM Solutions Engineer",
        "category": "DATA SCIENCE & AI",
        "required_skills": ["Python", "Generative AI", "Large Language Models", "LLM", "PyTorch"],
        "bonus_skills": ["FastAPI", "Docker", "Vector Databases", "LangChain", "RAG"],
        "min_experience_years": 1,
        "market_demand": "Skyrocketing",
        "salary_range": "$125,000 - $190,000 / ₹15 - 40 LPA",
        "growth_path": "AI Engineer → Principal AI Architect → Head of GenAI Transformation",
        "description": "Constructs modern Generative AI pipelines, Retrieval-Augmented Generation (RAG) agents, and customized LLM fine-tuning solutions."
    },

    # ------------------- CLOUD, DEVOPS & INFRASTRUCTURE -------------------
    {
        "id": "cloud-devops-eng",
        "title": "Cloud DevOps & Platform Engineer",
        "category": "CLOUD & DEVOPS",
        "required_skills": ["AWS", "Docker", "Kubernetes", "Git", "Linux", "CI/CD"],
        "bonus_skills": ["Terraform", "Ansible", "Jenkins", "Python", "Cloud Computing"],
        "min_experience_years": 1,
        "market_demand": "Very High",
        "salary_range": "$105,000 - $165,000 / ₹12 - 30 LPA",
        "growth_path": "DevOps Engineer → Site Reliability Engineer (SRE) → VP of Infrastructure",
        "description": "Automates continuous integration and delivery (CI/CD), provisions infrastructure-as-code, and orchestrates containerized cloud clusters."
    },
    {
        "id": "cybersecurity-analyst",
        "title": "Cybersecurity & Security Operations Analyst",
        "category": "CYBERSECURITY & NETWORKING",
        "required_skills": ["Cybersecurity", "Network Security", "Networking", "TCP/IP", "Firewall"],
        "bonus_skills": ["Ethical Hacking", "Penetration Testing", "Cryptography", "Linux", "SIEM"],
        "min_experience_years": 1,
        "market_demand": "Very High",
        "salary_range": "$90,000 - $145,000 / ₹9 - 24 LPA",
        "growth_path": "Security Analyst → Senior Security Architect → Chief Information Security Officer (CISO)",
        "description": "Monitors digital assets for vulnerabilities, hardens infrastructure, mitigates intrusion events, and enforces zero-trust protocols."
    },

    # ------------------- FINANCE & ACCOUNTING -------------------
    {
        "id": "financial-analyst",
        "title": "Financial Analyst & Reporting Specialist",
        "category": "ACCOUNTING & FINANCE",
        "required_skills": ["Accounting", "Financial Analysis", "Financial Reporting", "Budgeting", "Excel"],
        "bonus_skills": ["Financial Planning", "Cost Accounting", "Auditing", "Power BI"],
        "min_experience_years": 1,
        "market_demand": "High",
        "salary_range": "$75,000 - $120,000 / ₹7 - 18 LPA",
        "growth_path": "Financial Analyst → Finance Manager → Director of FP&A / CFO",
        "description": "Evaluates corporate financial statements, forecasts cash flows, oversees variance analysis, and delivers financial reporting."
    },
    {
        "id": "corporate-accountant",
        "title": "Senior Corporate Accountant (Tally / GST / Audit)",
        "category": "ACCOUNTING & FINANCE",
        "required_skills": ["Accounting", "Bookkeeping", "Taxation", "GST", "Tally", "Accounts Payable"],
        "bonus_skills": ["Accounts Receivable", "Auditing", "Payroll", "QuickBooks"],
        "min_experience_years": 1,
        "market_demand": "High",
        "salary_range": "$60,000 - $95,000 / ₹5 - 14 LPA",
        "growth_path": "Accountant → Senior Accountant → Financial Controller",
        "description": "Maintains statutory compliance, ledgers, tax filings (GST/Corporate Tax), bank reconciliations, and payroll disbursement."
    },

    # ------------------- SALES & DIGITAL MARKETING -------------------
    {
        "id": "digital-marketing-specialist",
        "title": "Digital Marketing & Growth Specialist",
        "category": "SALES & MARKETING",
        "required_skills": ["Digital Marketing", "SEO", "Social Media Marketing", "Content Marketing"],
        "bonus_skills": ["SEM", "Email Marketing", "Google Analytics", "Lead Generation", "CRM"],
        "min_experience_years": 0,
        "market_demand": "High",
        "salary_range": "$60,000 - $105,000 / ₹5 - 16 LPA",
        "growth_path": "Growth Marketer → Head of Digital Acquisition → Chief Marketing Officer (CMO)",
        "description": "Drives organic acquisition, search ranking visibility, conversion rate optimization, and multi-channel campaign ROI."
    },

    # ------------------- HUMAN RESOURCES & MANAGEMENT -------------------
    {
        "id": "technical-recruiter-hr",
        "title": "Talent Acquisition & HR Generalist",
        "category": "HUMAN RESOURCES",
        "required_skills": ["Human Resources", "Recruitment", "Talent Acquisition", "Employee Relations"],
        "bonus_skills": ["Onboarding", "Performance Management", "HRIS", "Payroll Management"],
        "min_experience_years": 1,
        "market_demand": "High",
        "salary_range": "$65,000 - $110,000 / ₹6 - 16 LPA",
        "growth_path": "Talent Recruiter → HR Business Partner (HRBP) → Chief People Officer (CPO)",
        "description": "Manages end-to-end recruitment pipelines, interview facilitation, candidate experience, and employee lifecycle management."
    },
    {
        "id": "technical-product-manager",
        "title": "Technical Product Manager (TPM)",
        "category": "MANAGEMENT & ADMINISTRATION",
        "required_skills": ["Project Management", "Agile", "Scrum", "Business Administration", "Strategic Planning"],
        "bonus_skills": ["SQL", "Data Analysis", "Jira", "API Design", "Team Management"],
        "min_experience_years": 2,
        "market_demand": "Very High",
        "salary_range": "$115,000 - $175,000 / ₹15 - 35 LPA",
        "growth_path": "Product Manager → Senior Product Manager → VP of Product",
        "description": "Aligns product roadmaps with business objectives, leads cross-functional engineering teams, and prioritizes feature development."
    }
]


# =======================================================================
# CAREER PREDICTION & MATCHING ENGINE
# =======================================================================

def predict_job_options(
    candidate_skills: List[str],
    resume_category: Optional[str] = None,
    experience_years: Optional[float] = None,
    resume_text: Optional[str] = None,
    top_n: int = 4
) -> List[Dict[str, Any]]:
    """
    Evaluates candidate skills against the job catalog and computes:
    - Match score percentage (blending skill overlap + bonus skills)
    - Demonstrated matched skills
    - Skills to learn (closing the gap)
    - Actionable customized justification/reasoning
    - Live job search URLs for LinkedIn, Indeed, and Glassdoor
    """
    candidate_skill_set = {s.strip().lower() for s in candidate_skills if s}

    recommendations: List[Dict[str, Any]] = []

    for job in JOB_CATALOG:
        required = job["required_skills"]
        bonus = job["bonus_skills"]

        # Calculate exact matching skills
        matched_req = [s for s in required if s.lower() in candidate_skill_set]
        matched_bonus = [s for s in bonus if s.lower() in candidate_skill_set]
        missing_req = [s for s in required if s.lower() not in candidate_skill_set]
        missing_bonus = [s for s in bonus if s.lower() not in candidate_skill_set]

        # Base overlap score
        req_ratio = len(matched_req) / max(1, len(required))
        bonus_ratio = len(matched_bonus) / max(1, len(bonus))

        # Weighted calculation (80% required skills, 20% bonus skills)
        base_score = (req_ratio * 80.0) + (bonus_ratio * 20.0)

        # Domain category alignment boost
        if resume_category and job["category"].upper() in resume_category.upper():
            base_score += 5.0

        # Clamp score between 0 and 99%
        fit_score = round(max(5.0, min(98.5, base_score)), 1)

        # Suitability classification
        if fit_score >= 75:
            suitability_label = "Prime Match"
            suitability_color = "#166534"
            suitability_bg = "#F0FDF4"
        elif fit_score >= 50:
            suitability_label = "High Growth Match"
            suitability_color = "#2563EB"
            suitability_bg = "#EFF6FF"
        elif fit_score >= 35:
            suitability_label = "Adjacent Pivot"
            suitability_color = "#D97706"
            suitability_bg = "#FFFBEB"
        else:
            suitability_label = "Future Horizon"
            suitability_color = "#64748B"
            suitability_bg = "#F8FAFC"

        # Generate intelligent reasoning text
        reasoning = _generate_justification(
            job=job,
            matched_req=matched_req,
            matched_bonus=matched_bonus,
            missing_req=missing_req,
            fit_score=fit_score
        )

        # Generate live search links
        encoded_title = urllib.parse.quote_plus(job["title"])
        linkedin_url = f"https://www.linkedin.com/jobs/search/?keywords={encoded_title}"
        indeed_url = f"https://www.indeed.com/jobs?q={encoded_title}"
        glassdoor_url = f"https://www.glassdoor.com/Job/jobs.htm?sc.keyword={encoded_title}"

        recommendations.append({
            "id": job["id"],
            "title": job["title"],
            "category": job["category"],
            "fit_score": fit_score,
            "suitability_label": suitability_label,
            "suitability_color": suitability_color,
            "suitability_bg": suitability_bg,
            "matched_skills": matched_req + matched_bonus,
            "skills_to_learn": missing_req[:4],
            "bonus_skills_to_learn": missing_bonus[:3],
            "reasoning": reasoning,
            "salary_range": job["salary_range"],
            "market_demand": job["market_demand"],
            "growth_path": job["growth_path"],
            "description": job["description"],
            "links": {
                "linkedin": linkedin_url,
                "indeed": indeed_url,
                "glassdoor": glassdoor_url
            }
        })

    # Sort descending by fit_score
    recommendations.sort(key=lambda item: item["fit_score"], reverse=True)
    return recommendations[:top_n]


def _generate_justification(
    job: Dict[str, Any],
    matched_req: List[str],
    matched_bonus: List[str],
    missing_req: List[str],
    fit_score: float
) -> str:
    """Generates personalized, constructive rationale explaining why this career path fits."""
    title = job["title"]
    all_matched = matched_req + matched_bonus

    if fit_score >= 70:
        if all_matched:
            matched_str = ", ".join(all_matched[:4])
            text = (
                f"Your demonstrated proficiencies in **{matched_str}** provide a direct foundation for the "
                f"core responsibilities of a {title}. You possess the foundational technical vocabulary "
                f"and tools required to clear hiring screens and contribute productively from day one."
            )
        else:
            text = (
                f"Your background exhibits strong domain synergy with {title}. With your core strengths, "
                f"you can step into this role with minimal onboarding overhead."
            )
    elif fit_score >= 45:
        if all_matched:
            matched_str = ", ".join(all_matched[:3])
            missing_str = ", ".join(missing_req[:2]) if missing_req else "specialized industry workflows"
            text = (
                f"You already demonstrate key overlapping strengths in **{matched_str}**. "
                f"Upskilling in **{missing_str}** would close the final gap and make you a high-conviction "
                f"candidate for {title} openings."
            )
        else:
            text = (
                f"This represents an excellent career growth opportunity. Your experience provides an "
                f"adaptable baseline that can be transitioned into {title} positions with targeted upskilling."
            )
    else:
        missing_str = ", ".join(missing_req[:3]) if missing_req else "domain tooling"
        text = (
            f"An ambitious adjacent career path. To effectively pivot into {title}, focus on developing "
            f"core competencies in **{missing_str}** through hands-on portfolio projects."
        )

    return text
