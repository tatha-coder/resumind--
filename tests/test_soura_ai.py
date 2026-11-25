import sys
from pathlib import Path
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
import sys
import json
from pathlib import Path
from llm_analyzer import analyze_resume

def run_test():
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1].strip().strip('"')
    elif sys.stdin.isatty():
        pdf_path = input("Enter your resume PDF path: ").strip().strip('"')
    else:
        pdf_path = "sample_resume.pdf"

    if not pdf_path or not Path(pdf_path).exists():
        print(f"Notice: No valid PDF file provided at '{pdf_path}'.")
        print("Usage: python test_soura_ai.py <path_to_resume.pdf>")
        return

    try:
        result = analyze_resume(pdf_path)

        print("\n===== RESUMIND AI =====")
        print(json.dumps(result, indent=4, ensure_ascii=False))

        print("\nAnalysis completed successfully!")

    except Exception as error:
        print("Error during resume analysis:", error)


if __name__ == "__main__":
    run_test()

