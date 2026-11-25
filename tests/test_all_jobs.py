import sys
from pathlib import Path
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from matcher import calculate_match

test_cases = [

    {
        "job": "IT Developer",
        "resume": "Python Java SQL Git Django",
        "description": "Required Python Java SQL Git Django"
    },

    {
        "job": "Digital Marketing",
        "resume": "SEO Social Media Marketing Google Analytics",
        "description": "SEO Content Marketing Social Media Marketing Google Analytics"
    },

    {
        "job": "Accountant",
        "resume": "Accounting Tally Microsoft Excel Financial Reporting",
        "description": "Accounting Tally Excel GST Financial Reporting"
    },

    {
        "job": "Human Resources",
        "resume": "Recruitment HR Management Communication Interviewing",
        "description": "Recruitment Employee Relations Interviewing Communication"
    },

    {
        "job": "Graphic Designer",
        "resume": "Photoshop Illustrator Canva Graphic Design",
        "description": "Photoshop Illustrator Figma Graphic Design"
    },

    {
        "job": "Teacher",
        "resume": "Teaching Lesson Planning Classroom Management",
        "description": "Teaching Curriculum Development Lesson Planning"
    }
]


for case in test_cases:

    print("\n" + "=" * 50)

    print("JOB:", case["job"])

    result = calculate_match(
        case["resume"],
        case["description"]
    )

    print("RESUME SKILLS:")
    print(result["resume_skills"])

    print("REQUIRED SKILLS:")
    print(result["required_skills"])

    print("MATCHED SKILLS:")
    print(result["matched_skills"])

    print("MISSING SKILLS:")
    print(result["missing_skills"])

    print("JOB MATCH SCORE:")
    print(result["match_score"])

