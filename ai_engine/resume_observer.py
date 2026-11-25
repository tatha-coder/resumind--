
import re
from pathlib import Path

import pymupdf


# =====================================================
# SOURA RESUME AI - UNIVERSAL RESUME OBSERVER
# Supports IT and NON-IT resume categories
# =====================================================

SKILL_DATABASE = {
    "IT & SOFTWARE": [
        "Python", "Java", "C", "C++", "C#", "JavaScript",
        "TypeScript", "PHP", "Ruby", "Go", "Rust", "Kotlin",
        "Swift", "R", "Dart", "Scala", "Perl", "MATLAB",
        "HTML", "CSS", "React", "Angular", "Vue", "Node.js",
        "Express.js", "Django", "Flask", "FastAPI", "Spring Boot",
        ".NET", "ASP.NET", "Laravel", "Bootstrap", "Next.js"
    ],

    "DATABASE": [
        "SQL", "MySQL", "PostgreSQL", "MongoDB", "SQLite",
        "Oracle", "Redis", "Firebase", "Supabase",
        "Microsoft SQL Server", "Cassandra", "DynamoDB"
    ],

    "DATA SCIENCE & AI": [
        "Machine Learning", "Deep Learning", "Artificial Intelligence",
        "Natural Language Processing", "Computer Vision",
        "TensorFlow", "PyTorch", "Scikit-learn", "Pandas",
        "NumPy", "Matplotlib", "Seaborn", "Power BI", "Tableau",
        "Data Analysis", "Data Visualization", "Statistics",
        "Generative AI", "Large Language Models", "LLM",
        "Data Science", "Data Engineering"
    ],

    "CLOUD & DEVOPS": [
        "AWS", "Microsoft Azure", "Google Cloud", "Docker",
        "Kubernetes", "Jenkins", "Git", "GitHub", "GitLab",
        "Linux", "Terraform", "Ansible", "CI/CD",
        "Cloud Computing", "DevOps"
    ],

    "CYBERSECURITY & NETWORKING": [
        "Cybersecurity", "Network Security", "Ethical Hacking",
        "Penetration Testing", "Cryptography", "Firewall",
        "Cisco", "Networking", "TCP/IP", "DNS", "VPN",
        "Wireshark", "Nmap", "SIEM", "Incident Response"
    ],

    "ACCOUNTING & FINANCE": [
        "Accounting", "Financial Accounting", "Bookkeeping",
        "Financial Reporting", "Financial Analysis", "Auditing",
        "Taxation", "GST", "Tally", "Tally ERP", "QuickBooks",
        "Accounts Payable", "Accounts Receivable",
        "Budgeting", "Payroll", "Cost Accounting",
        "Financial Planning", "Bank Reconciliation"
    ],

    "SALES & MARKETING": [
        "Sales", "Digital Marketing", "SEO", "SEM",
        "Social Media Marketing", "Content Marketing",
        "Email Marketing", "Lead Generation", "CRM",
        "Market Research", "Brand Management", "Advertising",
        "Customer Acquisition", "Salesforce", "HubSpot"
    ],

    "HUMAN RESOURCES": [
        "Human Resources", "Recruitment", "Talent Acquisition",
        "Employee Relations", "Payroll Management",
        "Performance Management", "HR Operations",
        "Training and Development", "HRIS", "Onboarding"
    ],

    "MANAGEMENT & ADMINISTRATION": [
        "Project Management", "Team Management",
        "Operations Management", "Business Administration",
        "Strategic Planning", "Business Development",
        "Office Administration", "Documentation",
        "Supply Chain Management", "Inventory Management",
        "Logistics", "Vendor Management"
    ],

    "CUSTOMER SERVICE & HOSPITALITY": [
        "Customer Service", "Customer Support",
        "Client Relationship Management", "Communication",
        "Complaint Resolution", "Guest Relations",
        "Hotel Management", "Front Office Operations",
        "Reservation Management", "Food and Beverage Service"
    ],

    "ENGINEERING & MANUFACTURING": [
        "AutoCAD", "SolidWorks", "CATIA", "Revit",
        "ANSYS", "PLC", "SCADA", "Quality Control",
        "Quality Assurance", "Production Planning",
        "Mechanical Design", "Electrical Maintenance",
        "Lean Manufacturing", "Six Sigma"
    ],

    "HEALTHCARE": [
        "Patient Care", "Clinical Documentation",
        "Medical Coding", "Medical Billing",
        "Healthcare Administration", "Nursing",
        "Phlebotomy", "First Aid", "Medical Records"
    ],

    "EDUCATION": [
        "Teaching", "Lesson Planning", "Curriculum Development",
        "Classroom Management", "Student Assessment",
        "Educational Technology", "Academic Research",
        "Training", "Mentoring"
    ],

    "GENERAL PROFESSIONAL SKILLS": [
        "Leadership", "Teamwork", "Problem Solving",
        "Critical Thinking", "Time Management",
        "Decision Making", "Adaptability",
        "Interpersonal Skills", "Negotiation",
        "Presentation Skills", "Written Communication"
    ]
}


SECTION_ALIASES = {
    "professional_summary": [
        "professional summary", "summary", "profile",
        "career profile", "professional profile",
        "about me", "executive summary", "overview",
        "career summary", "background summary", "bio"
    ],

    "objective": [
        "career objective", "objective",
        "career goal", "professional objective", "job objective"
    ],

    "education": [
        "education", "academic background",
        "educational qualifications", "academic qualifications",
        "academics", "education & credentials", "academic history",
        "education & training", "academic details", "qualifications"
    ],

    "experience": [
        "work experience", "professional experience",
        "employment history", "career history",
        "experience", "internship experience", "internships",
        "work history", "relevant experience", "practical experience"
    ],

    "skills": [
        "skills", "technical skills", "core competencies",
        "key skills", "areas of expertise", "professional skills",
        "competencies", "technologies", "tools & technologies",
        "tech stack", "tools and technologies", "programming skills",
        "technical expertise", "skills & tools"
    ],

    "projects": [
        "projects", "academic projects", "personal projects",
        "key projects", "project work", "technical projects"
    ],

    "certifications": [
        "certifications", "certificates", "licenses",
        "training and certifications", "certifications & professional development",
        "professional development", "courses & certifications",
        "certifications & courses", "certifications and licenses",
        "credentials", "trainings", "workshops & certifications"
    ],

    "achievements": [
        "achievements", "awards", "honors", "accomplishments",
        "key achievements", "awards & achievements", "honors & awards"
    ],

    "languages": [
        "languages", "language proficiency", "languages known"
    ],

    "interests": [
        "interests", "hobbies", "activities", "extracurricular activities"
    ],

    "additional_information": [
        "additional information", "other information", "miscellaneous",
        "general information", "extra details"
    ],

    "references": [
        "references", "referees"
    ]
}


# =====================================================
# PDF TEXT EXTRACTION
# =====================================================

def extract_pdf_text(file_path):

    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if file_path.suffix.lower() != ".pdf":
        raise ValueError("This version accepts PDF files only.")

    text = []

    with pymupdf.open(file_path) as document:

        for page in document:

            # Attempt sorted text extraction first for layout reading order
            page_text = page.get_text("text", sort=True)

            # Fall back to blocks if page_text is empty or unformatted
            if not page_text or len(page_text.strip()) < 15:
                blocks = page.get_text("blocks")
                page_text = "\n".join(b[4] for b in blocks if len(b) > 4 and str(b[4]).strip())

            if page_text.strip():
                text.append(page_text)

    full_text = "\n".join(text)
    full_text = full_text.replace("\xa0", " ")
    return full_text


# =====================================================
# TEXT CLEANING
# =====================================================

def clean_text(text):

    text = text.replace("\x00", " ")
    text = text.replace("\xa0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


# =====================================================
# CONTACT & PERSONAL INFORMATION
# =====================================================

def extract_name(text):
    """Identify the candidate's name from the top header lines of the resume."""
    excluded = [
        "resume", "curriculum vitae", "cv", "portfolio", "contact",
        "email", "phone", "mobile", "linkedin", "github", "profile",
        "summary", "objective", "address", "education", "experience",
        "skills", "page", "developer", "engineer"
    ]
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    for line in lines[:10]:
        clean_line = re.sub(r"^[•*|✦\s\d\.-]+", "", line).strip()
        words = clean_line.split()
        # Candidate names are typically 1 to 4 capitalized words without numbers or emails
        if (
            1 <= len(words) <= 4
            and len(clean_line) <= 45
            and not re.search(r"[@\d:/\\{}<>]", clean_line)
            and not any(exc in clean_line.lower() for exc in excluded)
            and any(c.isalpha() for c in clean_line)
        ):
            return clean_line
    return "Candidate"


def extract_email(text):

    pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"

    matches = re.findall(pattern, text)

    return list(dict.fromkeys(matches))


def extract_phone(text):

    # Match Indian 10-digit mobile (+91 / 9XXXXXXXXX), US, and international formats
    pattern = r"(?:\+?\d{1,3}[\s.-]?)?(?:\(?\d{2,5}\)?[\s.-]?)?\d{3,5}[\s.-]?\d{4,5}"

    matches = re.findall(pattern, text)
    cleaned = []
    for match in matches:
        digits = re.sub(r"\D", "", match)
        if 10 <= len(digits) <= 13:
            cleaned.append(match.strip())

    return list(dict.fromkeys(cleaned))


def extract_linkedin(text):
    match = re.search(r"(?:https?://)?(?:www\.)?linkedin\.com/(?:in|pub)/[a-zA-Z0-9_\-]+", text, re.IGNORECASE)
    return match.group(0) if match else ""


def extract_github(text):
    match = re.search(r"(?:https?://)?(?:www\.)?github\.com/[a-zA-Z0-9_\-]+", text, re.IGNORECASE)
    return match.group(0) if match else ""


def extract_links(text):

    pattern = r"(?:https?://|www\.)[^\s,;]+"

    matches = re.findall(pattern, text, flags=re.IGNORECASE)

    return list(dict.fromkeys(matches))


# =====================================================
# SECTION DETECTION
# =====================================================

def is_section_header(line):
    """Determines whether a line is a section boundary header."""
    clean_line = re.sub(r"^[\s\d\.\-•✦*|#:]+\s*", "", line).strip()
    clean_line = re.sub(r"[:\-|]+$", "", clean_line).strip()
    if not clean_line or len(clean_line) > 55:
        return None

    norm = clean_line.lower()

    # Direct match in aliases
    for sec, aliases in SECTION_ALIASES.items():
        if norm in aliases:
            return sec

    # Prefix or word-boundary match for compound headings
    for sec, aliases in SECTION_ALIASES.items():
        for alias in aliases:
            if norm == alias:
                return sec
            if norm.startswith(alias + " ") or norm.endswith(" " + alias):
                return sec
            if len(alias) >= 6 and re.search(r'\b' + re.escape(alias) + r'\b', norm):
                return sec

    return None


def identify_sections(text):

    sections = {
        name: [] for name in SECTION_ALIASES
    }

    current_section = "other"
    intro_lines = []

    for line in text.splitlines():

        stripped = line.strip()

        if not stripped:
            continue

        detected_section = None
        colon_content = None

        if ":" in stripped:
            parts = stripped.split(":", 1)
            hdr = is_section_header(parts[0])
            if hdr and parts[1].strip():
                detected_section = hdr
                colon_content = parts[1].strip()

        if not detected_section:
            detected_section = is_section_header(stripped)

        if detected_section:
            current_section = detected_section
            if colon_content and current_section in sections:
                sections[current_section].append(colon_content)
            continue

        if current_section == "other":
            intro_lines.append(stripped)
        elif current_section in sections:
            sections[current_section].append(stripped)

    # If professional summary is empty, see if introductory lines contain a summary
    summary_text = "\n".join(sections["professional_summary"]).strip()
    if not summary_text and intro_lines:
        # Check lines after candidate contact details
        candidate_summary = []
        for line in intro_lines[1:6]:
            if len(line.split()) >= 6 and not re.search(r"[@\+]\d", line):
                candidate_summary.append(line)
        if candidate_summary:
            sections["professional_summary"] = candidate_summary

    return {
        key: "\n".join(value).strip()
        for key, value in sections.items()
    }


# =====================================================
# SKILL DETECTION
# =====================================================

def detect_skills(text):

    found = {}

    for category, skills in SKILL_DATABASE.items():

        category_matches = []

        for skill in skills:

            pattern = (
                r"(?<![a-zA-Z0-9])"
                + re.escape(skill)
                + r"(?![a-zA-Z0-9])"
            )

            if re.search(pattern, text, flags=re.IGNORECASE):
                category_matches.append(skill)

        if category_matches:
            found[category] = sorted(
                set(category_matches),
                key=str.lower
            )

    return found


# =====================================================
# CAREER CATEGORY DETECTION
# =====================================================

IT_CATEGORIES = {
    "IT & SOFTWARE",
    "DATABASE",
    "DATA SCIENCE & AI",
    "CLOUD & DEVOPS",
    "CYBERSECURITY & NETWORKING"
}


def classify_resume(skills):

    categories = [
        category
        for category, detected in skills.items()
        if detected
    ]

    it_matches = [
        category for category in categories
        if category in IT_CATEGORIES
    ]

    non_it_matches = [
        category for category in categories
        if category not in IT_CATEGORIES
        and category != "GENERAL PROFESSIONAL SKILLS"
    ]

    if it_matches and non_it_matches:
        return "HYBRID / MULTI-DOMAIN"

    if it_matches:
        return "IT"

    if non_it_matches:
        return "NON-IT"

    return "UNCLASSIFIED"


# =====================================================
# EXPERIENCE INDICATORS
# =====================================================

def detect_experience_years(text):

    patterns = [
        r"(\d+(?:\.\d+)?)\+?\s+years?\s+of\s+experience",
        r"(\d+(?:\.\d+)?)\+?\s+years?\s+experience"
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            flags=re.IGNORECASE
        )

        if match:
            return float(match.group(1))

    return None


# =====================================================
# MAIN RESUME OBSERVER
# =====================================================

def observe_resume(file_path):

    raw_text = extract_pdf_text(file_path)

    text = clean_text(raw_text)

    sections = identify_sections(text)

    skills = detect_skills(text)

    result = {

        "file_name": Path(file_path).name,

        "resume_category": classify_resume(skills),

        "personal_information": {
            "name": extract_name(text),
            "emails": extract_email(text),
            "phone_numbers": extract_phone(text),
            "linkedin": extract_linkedin(text),
            "github": extract_github(text),
            "links": extract_links(text)
        },

        "contact_information": {
            "name": extract_name(text),
            "emails": extract_email(text),
            "phone_numbers": extract_phone(text),
            "linkedin": extract_linkedin(text),
            "github": extract_github(text),
            "links": extract_links(text)
        },

        "professional_summary": sections["professional_summary"],

        "career_objective": sections["objective"],

        "education": sections["education"],

        "work_experience": sections["experience"],

        "skills": skills,

        "projects": sections["projects"],

        "certifications": sections["certifications"],

        "achievements": sections["achievements"],

        "languages": sections["languages"],

        "interests": sections["interests"],

        "references": sections["references"],

        "experience_years_mentioned": detect_experience_years(text),

        "full_text": text

    }

    return result


# =====================================================
# COMMAND LINE TEST
# =====================================================

if __name__ == "__main__":

    import sys
    import json

    if len(sys.argv) < 2:

        print(
            'Usage: python -m ai_engine.resume_observer "resume.pdf"'
        )

        sys.exit(1)

    resume_path = sys.argv[1]

    try:

        result = observe_resume(resume_path)

        print("\n========== SOURA RESUME AI ==========\n")

        print(
            json.dumps(
                result,
                indent=4,
                ensure_ascii=False
            )
        )

        print("\n========== ANALYSIS COMPLETED ==========")

    except Exception as error:

        print("Resume analysis failed:", error)
