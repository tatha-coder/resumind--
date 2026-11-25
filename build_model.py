import sys
import subprocess
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent

def run_step(step_name: str, script_path: str):
    print("\n" + "=" * 60)
    print(f"STEP: {step_name}")
    print(f"Executing: python {script_path}")
    print("=" * 60)

    result = subprocess.run(
        [sys.executable, str(ROOT_DIR / script_path)],
        cwd=str(ROOT_DIR),
        capture_output=False
    )

    if result.returncode != 0:
        print(f"\n[ERROR] Step failed with exit code {result.returncode}: {step_name}")
        sys.exit(result.returncode)

    print(f"[SUCCESS] Completed: {step_name}")


def main():
    print("""
============================================================
       RESUMIND AI — AUTOMATED MODEL BUILD PIPELINE
============================================================
""")

    # 1. Prepare Datasets
    run_step("1. Dataset Generation (Resumes & Job Descriptions)", "training/prepare_dataset.py")

    # 2. Train Skill Classifier
    run_step("2. Training Skill Classification Neural Network (SkillNet)", "training/train_skills.py")

    # 3. Train Matching Network
    run_step("3. Training Resume-to-Job Matching Network (MatchNet)", "training/train_matching.py")

    # 4. Verify Inference
    print("\n" + "=" * 60)
    print("STEP: 4. Testing End-to-End AI Inference")
    print("=" * 60)

    try:
        from ai_engine.inference import predict_skills
        sample_resume = "Full-stack developer with 3 years in Python, FastAPI, Docker, React, and SQL."
        predictions = predict_skills(sample_resume)

        print("\nVerification Test on Sample Resume:")
        print(f"Input: \"{sample_resume}\"\n")
        print("Detected Skills (Confidence > 50%):")
        for pred in predictions[:6]:
            status = "[MATCH]" if pred["predicted_present"] else "[NO]"
            print(f"  {status} {pred['skill']:<18}: {pred['confidence']*100:.1f}%")

        print("\n============================================================")
        print("       ALL AI MODELS SUCCESSFULLY BUILT & VERIFIED!")
        print("============================================================")
        print("Artifacts generated in /models:")
        print(" - soura_skill_model.pth (SkillNet checkpoint)")
        print(" - soura_vectorizer.joblib (Skill TF-IDF vectorizer)")
        print(" - resumind_match_model.pth (MatchNet checkpoint)")
        print(" - resumind_match_vectorizer.joblib (Match TF-IDF vectorizer)")
        print(" - skill_metadata.json & match_metadata.json")

    except Exception as e:
        print(f"[ERROR] Inference verification failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
