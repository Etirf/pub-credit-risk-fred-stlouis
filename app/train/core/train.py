from pathlib import Path
from uuid import uuid4

import joblib
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from utils.logger import get_logger

logger = get_logger(__name__)


def train_model(df: pd.DataFrame, output_dir: Path = Path("models")) -> Path:
    y = df["default"]
    X = df.drop(columns=["name", "default"])
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)

    model = LogisticRegression(max_iter=500, solver="liblinear").fit(Xtr, ytr)

    output_dir.mkdir(exist_ok=True)
    model_name = f"model_{uuid4().hex[:8]}"
    model_path = output_dir / f"{model_name}.pkl"
    joblib.dump(model, model_path)

    logger.info(f"Trained model saved -> {model_path}")
    return model_path
