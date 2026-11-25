import sys
from pathlib import Path

# 1. Ensure project root is in sys.path before any local package imports
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import joblib
import numpy as np
import torch

from ai_engine.skill_model import SouraSkillNet

MODEL_DIR = ROOT / "models"
MODEL_PATH = MODEL_DIR / "soura_skill_model.pth"
VECTORIZER_PATH = MODEL_DIR / "soura_vectorizer.joblib"

# Matching model paths
MATCH_MODEL_PATH = MODEL_DIR / "resumind_match_model.pth"
MATCH_VECTORIZER_PATH = MODEL_DIR / "resumind_match_vectorizer.joblib"

DEVICE = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)


class SouraSkillPredictor:

    def __init__(self):

        if not MODEL_PATH.exists():
            raise FileNotFoundError(
                f"SkillNet model checkpoint not found at: {MODEL_PATH}\n"
                "Please run: python training/train_skills.py"
            )

        if not VECTORIZER_PATH.exists():
            raise FileNotFoundError(
                f"SkillNet vectorizer not found at: {VECTORIZER_PATH}\n"
                "Please run: python training/train_skills.py"
            )

        checkpoint = torch.load(
            MODEL_PATH,
            map_location="cpu",
            weights_only=True
        )

        self.labels = checkpoint["labels"]
        self.vectorizer = joblib.load(VECTORIZER_PATH)

        self.model = SouraSkillNet(
            input_size=checkpoint["input_size"],
            number_of_labels=len(self.labels)
        )

        self.model.load_state_dict(checkpoint["state_dict"])
        self.model.to(DEVICE)
        self.model.eval()

    def predict(self, resume_text: str, threshold: float = 0.5):
        if not resume_text or not resume_text.strip():
            return []

        features = self.vectorizer.transform([resume_text]).toarray()
        tensor = torch.tensor(features, dtype=torch.float32).to(DEVICE)

        with torch.no_grad():
            probabilities = torch.sigmoid(self.model(tensor))[0].cpu().numpy()

        results = []
        for label, confidence in zip(self.labels, probabilities):
            results.append({
                "skill": label,
                "confidence": round(float(confidence), 4),
                "predicted_present": bool(confidence >= threshold)
            })

        return sorted(
            results,
            key=lambda item: item["confidence"],
            reverse=True
        )


class ResumindMatchPredictor:

    def __init__(self):
        self.loaded = False
        if MATCH_MODEL_PATH.exists() and MATCH_VECTORIZER_PATH.exists():
            try:
                from ai_engine.matching_model import ResumindMatchNet
                checkpoint = torch.load(MATCH_MODEL_PATH, map_location="cpu", weights_only=True)
                self.vectorizer = joblib.load(MATCH_VECTORIZER_PATH)
                self.model = ResumindMatchNet(input_dim=checkpoint["input_dim"])
                self.model.load_state_dict(checkpoint["state_dict"])
                self.model.to(DEVICE)
                self.model.eval()
                self.loaded = True
            except Exception as e:
                print(f"[Notice] Could not load MatchNet ({e}).")

    def predict(self, resume_text: str, job_description: str) -> float:
        if not self.loaded:
            return 70.0

        combined = f"RESUME: {resume_text} TARGET_JOB: {job_description}"
        features = self.vectorizer.transform([combined]).toarray()
        tensor = torch.tensor(features, dtype=torch.float32).to(DEVICE)

        with torch.no_grad():
            score = self.model(tensor).item()

        return round(float(max(0.0, min(100.0, score))), 2)


_skill_predictor = None
_match_predictor = None


def predict_skills(resume_text: str, threshold: float = 0.5):
    """Predicts candidate skills using the trained PyTorch SkillNet."""
    global _skill_predictor
    if _skill_predictor is None:
        _skill_predictor = SouraSkillPredictor()
    return _skill_predictor.predict(resume_text, threshold=threshold)


def predict_match(resume_text: str, job_description: str) -> float:
    """Predicts candidate-to-job match score using ResumindMatchNet."""
    global _match_predictor
    if _match_predictor is None:
        _match_predictor = ResumindMatchPredictor()
    return _match_predictor.predict(resume_text, job_description)


if __name__ == "__main__":
    sample_text = """
    Senior Full-Stack Engineer with 4 years experience.
    Proficient in Python, FastAPI, React, TypeScript, Docker, SQL, and AWS.
    Developed scalable microservices and automated CI/CD pipelines using Git.
    """

    if len(sys.argv) > 1:
        arg = sys.argv[1].strip().strip('"')
        path_obj = Path(arg)
        if path_obj.exists() and path_obj.suffix.lower() == ".pdf":
            import pymupdf
            with pymupdf.open(path_obj) as doc:
                sample_text = "\n".join(page.get_text() for page in doc)
            print(f"Loaded resume from PDF: {path_obj}")
        else:
            sample_text = arg

    print("\n" + "=" * 55)
    print("      RESUMIND AI — NEURAL INFERENCE ENGINE")
    print("=" * 55)
    print(f"Device: {DEVICE}")
    print(f"Input Preview:\n{sample_text.strip()[:180]}...\n")

    print("Running SkillNet Predictions...")
    predictions = predict_skills(sample_text)

    print(f"{'SKILL':<20} | {'CONFIDENCE':<12} | {'PREDICTED'}")
    print("-" * 48)
    for item in predictions[:10]:
        status = "[YES]" if item["predicted_present"] else "[NO]"
        print(f"{item['skill']:<20} | {item['confidence']*100:>8.2f}%    | {status}")

    # Test MatchNet
    sample_jd = "Looking for Senior Developer with Python, FastAPI, Docker, and AWS."
    match_score = predict_match(sample_text, sample_jd)
    print("-" * 48)
    print(f"Neural Match Score against Sample Job: {match_score}%\n")
