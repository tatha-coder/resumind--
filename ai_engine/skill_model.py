
import torch
# pyrefly: ignore[missing-import]
from torch import nn


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
