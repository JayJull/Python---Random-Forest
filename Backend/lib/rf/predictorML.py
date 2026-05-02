import os
import pickle
import pandas as pd

from lib.rf.interfaceML import PredictionInput, PredictionResult

MODEL_PATH = os.path.join(os.path.dirname(__file__), "model.pkl")

_model = None


def _load_model():
    global _model
    if _model is None:
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(f"Model file not found: {MODEL_PATH}")
        with open(MODEL_PATH, "rb") as f:
            _model = pickle.load(f)
    return _model


def run_prediction(inputs: list[PredictionInput]) -> list[PredictionResult]:
    model = _load_model()

    features = pd.DataFrame(
        [[item.rating, item.jumlah_ulasan, item.website] for item in inputs],
        columns=["Rating", "Jumlah Ulasan", "Website"],
    )

    predictions   = model.predict(features)
    probabilities = model.predict_proba(features)

    return [
        PredictionResult(
            status     = "Prospek" if int(pred) == 1 else "Belum Prospek",
            confidence = round(float(max(prob)), 4),
        )
        for pred, prob in zip(predictions, probabilities)
    ]