from dataclasses import dataclass
from typing import Literal

@dataclass
class PredictionInput:
    rating:        float
    jumlah_ulasan: int
    website:       int


@dataclass
class PredictionResult:
    status:     Literal["Prospek", "Belum Prospek"]
    confidence: float