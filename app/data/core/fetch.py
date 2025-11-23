import pandas as pd
import numpy as np
from faker import Faker
from fredapi import Fred
from pathlib import Path
from utils.logger import get_logger
from utils.cache import load_cache, save_cache
from settings import settings


MACRO_CACHE_DIR = Path("storage/macro_cache")
MACRO_CACHE_DIR.mkdir(parents=True, exist_ok=True)

logger = get_logger(__name__)

def get_macro_data(fields: list[str] | None = None, use_cache=True) -> dict:
    fred = Fred(api_key=settings.fred_api_key)
    mapping = {
        "TDSP": "debt_ratio",
        "DRCCLACBS": "delinquency",
        "FEDFUNDS": "interest_rate",
    }
    selected = [sid for sid, name in mapping.items() if not fields or name in fields]

    results = {}
    for sid in selected:
        try:
            series = fred.get_series(sid)
            val = float(series.dropna().iloc[-1])
            save_cache(MACRO_CACHE_DIR / f"{sid}.pkl", {sid: val})
            results[mapping[sid]] = val
        except Exception:
            cache = load_cache(MACRO_CACHE_DIR / f"{sid}.pkl")
            results[mapping[sid]] = cache.get(sid, 0.0)
            logger.warning(f"Fallback for {sid}: {results[mapping[sid]]}")
    return results

def generate_synthetic_data(macro_data: dict, n=1000) -> pd.DataFrame:
    fake = Faker()
    rows = []
    for _ in range(n):
        inc = np.random.normal(4000, 1500)
        loan = np.random.normal(10000, 5000)
        util = loan / (inc + 1)
        risk = util * (1 + macro_data["delinquency"]/100)
        default = int(risk > np.random.uniform(1, 3))
        rows.append({
            "name": fake.name(),
            "monthly_income": round(inc, 2),
            "loan_amount": round(loan, 2),
            "utilization": round(util, 3),
            "interest_rate": macro_data["interest_rate"],
            "debt_ratio": macro_data["debt_ratio"],
            "default": default
        })
    return pd.DataFrame(rows)
