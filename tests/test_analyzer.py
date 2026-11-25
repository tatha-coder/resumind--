import sys
from pathlib import Path
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
import sys
from pathlib import Path
import pymupdf
from llm_analyzer import analyse_resume

print("===== RESUMIND AI TEST ANALYZER =====")

pdf_path = None
job_description = None

if len(sys.argv) > 2:
    pdf_path = sys.argv[1].strip().strip('"')
    job_description = sys.argv[2].strip()
elif len(sys.argv) > 1:
    pdf_path = sys.argv[1].strip().strip('"')
elif sys.stdin.isatty():
    pdf_path = input("\nEnter PDF resume path: ").strip().strip('"')

if pdf_path and pdf_path.startswith("file:///"):
    pdf_path = pdf_path.replace("file:///", "").replace("/", "\\")

if pdf_path and Path(pdf_path).exists():
    try:
        document = pymupdf.open(pdf_path)
        resume_text = "\n".join(page.get_text() for page in document)
        document.close()
        print(f"\nResume extracted successfully from: {pdf_path}")
    except Exception as e:
        print("\nPDF extraction error:", e)
        sys.exit(1)
else:
    print("\nNo PDF path provided. Using built-in sample candidate profile for verification:")
    resume_text = """
    Jane Doe - Senior Full-Stack Engineer
    Skills: Python, FastAPI, React, TypeScript, Docker, SQL, AWS, Git
    Experience: 4 years developing scalable REST APIs, microservices, and web applications.
    Education: B.Tech in Computer Science
    """
    print(resume_text.strip())

if not job_description:
    if sys.stdin.isatty() and pdf_path:
        job_description = input("\nEnter job description: ").strip()
    else:
        job_description = "Looking for Senior Full-Stack Developer skilled in Python, FastAPI, Docker, and PostgreSQL on AWS."

print(f"\nTarget Job Description: {job_description}")
print("\nAnalysing resume with Resumind Intelligence... Please wait.\n")

try:
    result = analyse_resume(resume_text, job_description)
    print("===== RESUME ANALYSIS REPORT =====\n")
    print(result)
except Exception as e:
    print("\nAnalysis Error:", e)

