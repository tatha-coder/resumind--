import sys
from pathlib import Path
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from matcher import calculate_match

resume = """
Python Java SQL Excel
"""

job_description = """
Required skills:
Python Java SQL Git Django
"""

result = calculate_match(resume, job_description)

print("\n========== JOB SUITABILITY TEST ==========")

print("\n1. RESUME SKILLS:")
print(result["resume_skills"])

print("\n2. REQUIRED JOB SKILLS:")
print(result["required_skills"])

print("\n3. MATCHED SKILLS:")
print(result["matched_skills"])

print("\n4. MISSING SKILLS:")
print(result["missing_skills"])

print("\n5. JOB SUITABILITY:")
print(result["match_score"], "%")

print("\n========== TEST COMPLETED ==========")

