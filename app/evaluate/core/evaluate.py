import pandas as pd
import joblib
from sklearn.metrics import roc_auc_score
from utils.logger import get_logger

logger = get_logger(__name__)

def evaluate_model(df: pd.DataFrame, model_path) -> float:
    y = df["default"]
    X = df.drop(columns=["name", "default"])
    model = joblib.load(model_path)
    preds = model.predict_proba(X)[:, 1]
    auc = roc_auc_score(y, preds)
    logger.info(f"AUC Score: {auc:.3f}")
    return auc
