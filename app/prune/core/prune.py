import pandas as pd
import joblib
from sklearn.feature_selection import SelectFromModel
from sklearn.linear_model import LogisticRegression
from pathlib import Path
from utils.logger import get_logger

logger = get_logger(__name__)

def prune_model(df: pd.DataFrame, model_path: Path) -> Path:
    y = df["default"]
    X = df.drop(columns=["name", "default"])

    base = joblib.load(model_path)
    selector = SelectFromModel(base, prefit=True, threshold="mean")
    Xr = selector.transform(X)
    pruned = LogisticRegression(max_iter=500, solver="liblinear").fit(Xr, y)

    pruned_path = model_path.with_name(model_path.stem + "_pruned.pkl")
    joblib.dump((selector, pruned), pruned_path)

    logger.info(f"Pruned model saved -> {pruned_path}")
    return pruned_path
