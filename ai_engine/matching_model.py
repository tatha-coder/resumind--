import torch
from torch import nn


class ResumindMatchNet(nn.Module):
    """
    Deep neural network for scoring resume-to-job compatibility.
    Evaluates concatenated semantic features, n-gram overlap, and cross-attention signals.
    Outputs a continuous suitability score between 0.0 and 100.0.
    """

    def __init__(self, input_dim: int):
        super().__init__()

        self.dense_block = nn.Sequential(
            nn.Linear(input_dim, 256),
            nn.BatchNorm1d(256),
            nn.ReLU(),
            nn.Dropout(0.25),

            nn.Linear(256, 128),
            nn.BatchNorm1d(128),
            nn.ReLU(),
            nn.Dropout(0.20),

            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Dropout(0.10),

            nn.Linear(64, 1),
            nn.Sigmoid()
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # Scale Sigmoid output (0.0 to 1.0) into percentage range (0.0 to 100.0)
        return self.dense_block(x) * 100.0


class ResumindCrossEncoder(nn.Module):
    """
    Siamese dual-encoder that projects resume and job embeddings into a shared latent space,
    measuring alignment through learned non-linear projections.
    """

    def __init__(self, vocab_size: int, embedding_dim: int = 64):
        super().__init__()

        # Shared projection trunk
        self.encoder = nn.Sequential(
            nn.Linear(vocab_size, 128),
            nn.ReLU(),
            nn.Linear(128, embedding_dim),
            nn.LayerNorm(embedding_dim)
        )

        # Scorer
        self.classifier = nn.Sequential(
            nn.Linear(embedding_dim * 3, 64),
            nn.ReLU(),
            nn.Linear(64, 1),
            nn.Sigmoid()
        )

    def forward(self, resume_vec: torch.Tensor, jd_vec: torch.Tensor) -> torch.Tensor:
        u = self.encoder(resume_vec)
        v = self.encoder(jd_vec)
        # Combine embeddings: [u, v, |u - v|]
        diff = torch.abs(u - v)
        features = torch.cat([u, v, diff], dim=1)
        return self.classifier(features) * 100.0
