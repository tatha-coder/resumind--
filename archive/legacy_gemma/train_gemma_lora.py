
from pathlib import Path
import json

import joblib
import numpy as np
import pandas as pd
import torch

from torch import nn
from torch.utils.data import DataLoader, TensorDataset

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import f1_score

# =====================================================
# 1. PROJECT PATHS
# =====================================================

ROOT = Path(__file__).resolve().parents[1]

TRAIN_FILE = ROOT / "dataset" / "skills_train.csv"
VALID_FILE = ROOT / "dataset" / "skills_validation.csv"

MODEL_DIR = ROOT / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

MODEL_PATH = MODEL_DIR / "soura_skill_model.pth"
VECTORIZER_PATH = MODEL_DIR / "soura_vectorizer.joblib"
METADATA_PATH = MODEL_DIR / "model_metadata.json"

# =====================================================
# 2. TRAINING CONFIGURATION
# =====================================================

EPOCHS = 40
BATCH_SIZE = 8
LEARNING_RATE = 0.001

DEVICE = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)

print("=" * 50)
print("SOURA SKILLNET - TRAINING FROM SCRATCH")
print("=" * 50)
print("Device:", DEVICE)

if torch.cuda.is_available():
    print("GPU:", torch.cuda.get_device_name(0))

# =====================================================
# 3. DEFINE NEURAL NETWORK
# =====================================================

class SouraSkillNet(nn.Module):

    def __init__(self, input_size, number_of_labels):

        super().__init__()

        self.network = nn.Sequential(

            nn.Linear(input_size, 128),
            nn.ReLU(),
            nn.Dropout(0.20),

            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Dropout(0.15),

            nn.Linear(64, number_of_labels)
        )

    def forward(self, x):
        return self.network(x)


# =====================================================
# 4. VERIFY DATASET
# =====================================================

if not TRAIN_FILE.exists():
    raise FileNotFoundError(
        f"Training file missing: {TRAIN_FILE}"
    )

if not VALID_FILE.exists():
    raise FileNotFoundError(
        f"Validation file missing: {VALID_FILE}"
    )

train_df = pd.read_csv(TRAIN_FILE).fillna("")
valid_df = pd.read_csv(VALID_FILE).fillna("")

if "resume_text" not in train_df.columns:
    raise ValueError(
        "Training CSV must contain a resume_text column."
    )

if "resume_text" not in valid_df.columns:
    raise ValueError(
        "Validation CSV must contain a resume_text column."
    )

LABELS = [
    column for column in train_df.columns
    if column != "resume_text"
]

if not LABELS:
    raise ValueError("No skill labels found in training CSV.")

if LABELS != [
    column for column in valid_df.columns
    if column != "resume_text"
]:
    raise ValueError(
        "Training and validation columns must match exactly."
    )

train_texts = train_df["resume_text"].astype(str).tolist()
valid_texts = valid_df["resume_text"].astype(str).tolist()

if not train_texts or not valid_texts:
    raise ValueError("Training and validation datasets cannot be empty.")

y_train = train_df[LABELS].astype(float).to_numpy()
y_valid = valid_df[LABELS].astype(float).to_numpy()

if not np.isin(y_train, [0, 1]).all():
    raise ValueError("Training labels must contain only 0 and 1.")

if not np.isin(y_valid, [0, 1]).all():
    raise ValueError("Validation labels must contain only 0 and 1.")

if not np.isfinite(y_train).all() or not np.isfinite(y_valid).all():
    raise ValueError("Dataset contains invalid numeric labels.")

print("\nTraining examples:", len(train_texts))
print("Validation examples:", len(valid_texts))
print("Skills:", LABELS)

# =====================================================
# 5. LEARN TEXT VOCABULARY
# =====================================================

vectorizer = TfidfVectorizer(
    max_features=5000,
    ngram_range=(1, 2),
    sublinear_tf=True,
    stop_words="english"
)

x_train = vectorizer.fit_transform(
    train_texts
).toarray()

x_valid = vectorizer.transform(
    valid_texts
).toarray()

if x_train.shape[1] == 0:
    raise ValueError(
        "No vocabulary was learned. Check your resume text."
    )

print("Learned vocabulary size:", x_train.shape[1])

# =====================================================
# 6. CONVERT DATA TO PYTORCH TENSORS
# =====================================================

x_train = torch.tensor(
    x_train,
    dtype=torch.float32
)

y_train = torch.tensor(
    y_train,
    dtype=torch.float32
)

x_valid = torch.tensor(
    x_valid,
    dtype=torch.float32,
    device=DEVICE
)

y_valid = torch.tensor(
    y_valid,
    dtype=torch.float32,
    device=DEVICE
)

train_loader = DataLoader(
    TensorDataset(x_train, y_train),
    batch_size=BATCH_SIZE,
    shuffle=True
)

# =====================================================
# 7. INITIALISE MODEL FROM RANDOM WEIGHTS
# =====================================================

model = SouraSkillNet(
    input_size=x_train.shape[1],
    number_of_labels=len(LABELS)
).to(DEVICE)

loss_function = nn.BCEWithLogitsLoss()

optimizer = torch.optim.Adam(
    model.parameters(),
    lr=LEARNING_RATE
)

print("\nModel initialised from random weights.")
print("Training started...\n")

# =====================================================
# 8. TRAIN MODEL
# =====================================================

for epoch in range(EPOCHS):

    model.train()
    total_loss = 0.0

    for batch_x, batch_y in train_loader:

        batch_x = batch_x.to(DEVICE)
        batch_y = batch_y.to(DEVICE)

        optimizer.zero_grad()

        outputs = model(batch_x)

        loss = loss_function(
            outputs,
            batch_y
        )

        loss.backward()
        optimizer.step()

        total_loss += loss.item()

    # Validation
    model.eval()

    with torch.no_grad():

        predictions = torch.sigmoid(model(x_valid))

        predicted_labels = (
            predictions >= 0.5
        ).cpu().numpy()

        actual_labels = y_valid.cpu().numpy()

        validation_f1 = f1_score(
            actual_labels,
            predicted_labels,
            average="micro",
            zero_division=0
        )

    average_loss = total_loss / len(train_loader)

    print(
        f"Epoch {epoch + 1:02d}/{EPOCHS} | "
        f"Loss: {average_loss:.4f} | "
        f"Validation F1: {validation_f1:.4f}"
    )

# =====================================================
# 9. SAVE TRAINED MODEL
# =====================================================

model = model.cpu()

torch.save(
    {
        "state_dict": model.state_dict(),
        "input_size": x_train.shape[1],
        "labels": LABELS
    },
    MODEL_PATH
)

joblib.dump(
    vectorizer,
    VECTORIZER_PATH
)

metadata = {
    "model_name": "Soura SkillNet",
    "architecture": "TF-IDF + PyTorch Neural Network",
    "training_method": "Random initialization and supervised training",
    "labels": LABELS,
    "input_size": int(x_train.shape[1]),
    "epochs": EPOCHS,
    "validation_micro_f1": float(validation_f1)
}

with open(
    METADATA_PATH,
    "w",
    encoding="utf-8"
) as file:

    json.dump(
        metadata,
        file,
        indent=4
    )

print("\n" + "=" * 50)
print("SOURA SKILLNET TRAINING COMPLETE")
print("=" * 50)

print("Model:", MODEL_PATH)
print("Vectorizer:", VECTORIZER_PATH)
print("Metadata:", METADATA_PATH)
print("Validation micro-F1:", round(validation_f1, 4))
