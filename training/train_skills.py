from pathlib import Path
import json

import joblib
import numpy as np
import pandas as pd
import torch
import torch.nn as nn

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.metrics import f1_score, classification_report


# -----------------------------
# 1. Configuration
# -----------------------------

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_PATH = BASE_DIR / "dataset" / "resumes.csv"
if not DATA_PATH.exists():
    DATA_PATH = BASE_DIR / "training" / "datasets" / "resumes.csv"
MODEL_DIR = BASE_DIR / "models"

MODEL_DIR.mkdir(parents=True, exist_ok=True)

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

EPOCHS = 100
LEARNING_RATE = 0.001
BATCH_SIZE = 8

torch.manual_seed(42)
np.random.seed(42)

print("Training device:", DEVICE)

# -----------------------------
# 2. Load dataset
# -----------------------------

if not DATA_PATH.exists():
    raise FileNotFoundError(
        f"Dataset not found: {DATA_PATH}. "
        "Run training/prepare_dataset.py first."
    )

df = pd.read_csv(DATA_PATH)

# Dynamically extract all skill columns present in resumes.csv
skills = [col for col in df.columns if col != "resume_text"]
print(f"Loaded {len(df)} resumes across {len(skills)} skills:")
print(", ".join(skills))

X_text = df["resume_text"].fillna("").astype(str).tolist()
y = df[skills].values.astype(np.float32)

if len(df) < 10:
    raise ValueError("Please provide at least 10 labelled examples.")

# -----------------------------
# 3. Convert text to numbers
# -----------------------------

vectorizer = TfidfVectorizer(
    max_features=3000,
    ngram_range=(1, 2),
    lowercase=True,
    sublinear_tf=True
)

X = vectorizer.fit_transform(X_text).toarray().astype(np.float32)

# -----------------------------
# 4. Split training and testing
# -----------------------------

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42
)

X_train_tensor = torch.tensor(X_train, dtype=torch.float32, device=DEVICE)
y_train_tensor = torch.tensor(y_train, dtype=torch.float32, device=DEVICE)

X_test_tensor = torch.tensor(
    X_test, dtype=torch.float32, device=DEVICE
)

# -----------------------------
# 5. Define Neural Network
# -----------------------------

class SouraSkillNet(nn.Module):

    def __init__(self, input_size, output_size):
        super().__init__()

        self.network = nn.Sequential(
            nn.Linear(input_size, 128),
            nn.ReLU(),
            nn.Dropout(0.2),

            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Dropout(0.15),

            nn.Linear(64, output_size)
        )

    def forward(self, x):
        return self.network(x)


model = SouraSkillNet(
    input_size=X_train.shape[1],
    output_size=len(skills)
).to(DEVICE)

# -----------------------------
# 6. Define loss and optimizer
# -----------------------------

criterion = nn.BCEWithLogitsLoss()

optimizer = torch.optim.Adam(
    model.parameters(),
    lr=LEARNING_RATE
)

# -----------------------------
# 7. Train the model
# -----------------------------

print("\nStarting neural network training...")

for epoch in range(EPOCHS):

    model.train()

    indices = torch.randperm(X_train_tensor.size(0), device=DEVICE)

    total_loss = 0.0

    for start in range(0, X_train_tensor.size(0), BATCH_SIZE):

        batch_indices = indices[start:start + BATCH_SIZE]

        batch_x = X_train_tensor[batch_indices]
        batch_y = y_train_tensor[batch_indices]

        optimizer.zero_grad()

        outputs = model(batch_x)

        loss = criterion(outputs, batch_y)

        loss.backward()

        optimizer.step()

        total_loss += loss.item()

    if (epoch + 1) % 20 == 0 or (epoch + 1) == EPOCHS:
        average_loss = total_loss / (
            (X_train_tensor.size(0) + BATCH_SIZE - 1) // BATCH_SIZE
        )

        print(
            f"Epoch [{epoch + 1}/{EPOCHS}] "
            f"Loss: {average_loss:.4f}"
        )

# -----------------------------
# 8. Evaluate on test data
# -----------------------------

model.eval()

with torch.no_grad():
    test_logits = model(X_test_tensor)
    probabilities = torch.sigmoid(test_logits).cpu().numpy()

predictions = (probabilities >= 0.5).astype(int)

print("\nEvaluation results:")
print(
    classification_report(
        y_test,
        predictions,
        target_names=skills,
        zero_division=0
    )
)

micro_f1 = f1_score(
    y_test,
    predictions,
    average="micro",
    zero_division=0
)

print("Micro F1 score:", round(micro_f1, 4))

# -----------------------------
# 9. Save our trained model & checkpoint
# -----------------------------

checkpoint = {
    "state_dict": model.state_dict(),
    "labels": skills,
    "input_size": int(X_train.shape[1]),
    "hidden_layers": [128, 64],
    "micro_f1": float(micro_f1),
    "epochs": EPOCHS,
    "device_used": str(DEVICE)
}

# Save checkpoint loaded by ai_engine/inference.py
torch.save(checkpoint, MODEL_DIR / "soura_skill_model.pth")
torch.save(checkpoint, MODEL_DIR / "resumind_skill_model.pth")

# Save TF-IDF vectorizer
joblib.dump(vectorizer, MODEL_DIR / "soura_vectorizer.joblib")
joblib.dump(vectorizer, MODEL_DIR / "resumind_vectorizer.joblib")

metadata = {
    "skills": skills,
    "input_size": int(X_train.shape[1]),
    "hidden_layers": [128, 64],
    "device_used": str(DEVICE),
    "training_examples": len(X_train),
    "testing_examples": len(X_test),
    "micro_f1": round(float(micro_f1), 4),
    "epochs": EPOCHS,
    "model_type": "SouraSkillNet"
}

with open(MODEL_DIR / "skill_metadata.json", "w", encoding="utf-8") as file:
    json.dump(metadata, file, indent=4)

print("\nTraining completed successfully!")
print("Saved checkpoint:", MODEL_DIR / "soura_skill_model.pth")
print("Saved vectorizer:", MODEL_DIR / "soura_vectorizer.joblib")
print("Saved metadata:", MODEL_DIR / "skill_metadata.json")
