import sys
import json
from pathlib import Path
import numpy as np
import pandas as pd
import joblib
import torch
import torch.nn as nn
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from ai_engine.matching_model import ResumindMatchNet

DATA_PATH = BASE_DIR / "dataset" / "job_description.csv"
if not DATA_PATH.exists():
    DATA_PATH = BASE_DIR / "training" / "datasets" / "job_description.csv"
MODEL_DIR = BASE_DIR / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

EPOCHS = 80
BATCH_SIZE = 16
LEARNING_RATE = 0.002

torch.manual_seed(42)
np.random.seed(42)

print("Training device for Matching Model:", DEVICE)

# -----------------------------
# 2. Load Dataset
# -----------------------------

if not DATA_PATH.exists():
    raise FileNotFoundError(
        f"Matching dataset not found at: {DATA_PATH}\n"
        "Run: python training/prepare_dataset.py"
    )

df = pd.read_csv(DATA_PATH)
print(f"Loaded {len(df)} paired resume-job records.")

# Combine resume text and job description into structured feature pairs
df["combined_text"] = (
    "RESUME: " + df["resume_text"].fillna("") +
    " TARGET_JOB: " + df["job_description"].fillna("") +
    " REQUIRED_SKILLS: " + df["target_skills"].fillna("")
)

X_text = df["combined_text"].tolist()
y = df["match_score"].values.astype(np.float32)

# -----------------------------
# 3. Vectorization
# -----------------------------

vectorizer = TfidfVectorizer(
    max_features=4000,
    ngram_range=(1, 2),
    sublinear_tf=True
)

X = vectorizer.fit_transform(X_text).toarray().astype(np.float32)

# -----------------------------
# 4. Train / Test Split
# -----------------------------

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.15, random_state=42
)

X_train_tensor = torch.tensor(X_train, dtype=torch.float32, device=DEVICE)
y_train_tensor = torch.tensor(y_train, dtype=torch.float32, device=DEVICE).unsqueeze(1)

X_test_tensor = torch.tensor(X_test, dtype=torch.float32, device=DEVICE)
y_test_tensor = torch.tensor(y_test, dtype=torch.float32, device=DEVICE).unsqueeze(1)

# -----------------------------
# 5. Initialize ResumindMatchNet
# -----------------------------

model = ResumindMatchNet(input_dim=X_train.shape[1]).to(DEVICE)

criterion = nn.MSELoss()
optimizer = torch.optim.AdamW(model.parameters(), lr=LEARNING_RATE, weight_decay=1e-4)

# -----------------------------
# 6. Training Loop
# -----------------------------

print(f"\nTraining ResumindMatchNet on {len(X_train)} samples across {EPOCHS} epochs...")

for epoch in range(EPOCHS):
    model.train()
    indices = torch.randperm(X_train_tensor.size(0), device=DEVICE)
    total_loss = 0.0

    for start in range(0, X_train_tensor.size(0), BATCH_SIZE):
        batch_indices = indices[start:start + BATCH_SIZE]
        batch_x = X_train_tensor[batch_indices]
        batch_y = y_train_tensor[batch_indices]

        optimizer.zero_grad()
        predictions = model(batch_x)
        loss = criterion(predictions, batch_y)
        loss.backward()
        optimizer.step()

        total_loss += loss.item()

    if (epoch + 1) % 20 == 0 or (epoch + 1) == EPOCHS:
        avg_loss = total_loss / ((X_train_tensor.size(0) + BATCH_SIZE - 1) // BATCH_SIZE)
        print(f"Epoch [{epoch + 1}/{EPOCHS}] - MSE Loss: {avg_loss:.2f}")

# -----------------------------
# 7. Evaluation
# -----------------------------

model.eval()
with torch.no_grad():
    test_preds = model(X_test_tensor).cpu().numpy().flatten()

mae = mean_absolute_error(y_test, test_preds)
r2 = r2_score(y_test, test_preds)

print("\nModel Evaluation:")
print(f" - Mean Absolute Error (MAE): {mae:.2f} points")
print(f" - R² Calibration Score: {r2:.4f}")

# -----------------------------
# 8. Save Model & Checkpoint
# -----------------------------

checkpoint = {
    "state_dict": model.state_dict(),
    "input_dim": int(X_train.shape[1]),
    "mae": float(mae),
    "r2": float(r2),
    "epochs": EPOCHS,
    "device": str(DEVICE)
}

torch.save(checkpoint, MODEL_DIR / "resumind_match_model.pth")
joblib.dump(vectorizer, MODEL_DIR / "resumind_match_vectorizer.joblib")

metadata = {
    "model_name": "ResumindMatchNet",
    "input_dim": int(X_train.shape[1]),
    "mae": round(float(mae), 2),
    "r2_score": round(float(r2), 4),
    "epochs": EPOCHS,
    "training_samples": len(X_train),
    "test_samples": len(X_test)
}

with open(MODEL_DIR / "match_metadata.json", "w", encoding="utf-8") as f:
    json.dump(metadata, f, indent=4)

print("\nMatching model training complete!")
print("Saved model checkpoint:", MODEL_DIR / "resumind_match_model.pth")
print("Saved vectorizer:", MODEL_DIR / "resumind_match_vectorizer.joblib")
