import sys
import json
from pathlib import Path

from ai_engine.field_extractor import extract_field_analysis

if len(sys.argv) > 1:
    resume_path = sys.argv[1].strip().strip('"')
elif sys.stdin.isatty():
    resume_path = input("Enter the full path of your resume PDF: ").strip().strip('"')
else:
    resume_path = "sample_resume.pdf"

if not resume_path or not Path(resume_path).exists():
    print(f"Notice: No valid PDF file provided at '{resume_path}'.")
    print("Usage: python -m ai_engine.test_extractor <path_to_resume.pdf>")
    sys.exit(0)

try:
    result = extract_field_analysis(resume_path)

    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)

    output_file = output_dir / "resume_analysis.json"

    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(result, file, indent=4, ensure_ascii=False)

    print("\n===== RESUMIND FIELD EXTRACTOR ANALYSIS =====")
    print(json.dumps(result, indent=4, ensure_ascii=False))

    print("\nAnalysis saved to:", output_file)

except Exception as error:
    print("\nError during extraction:", error)
