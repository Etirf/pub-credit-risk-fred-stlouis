from pathlib import Path
from uuid import uuid4

from app.artifacts.infrastructure import log_dataset
from app.data.core import get_macro_data, generate_synthetic_data
from utils.logger import get_logger


DATASET_DIR = Path("storage/datasets")
DATASET_DIR.mkdir(parents=True, exist_ok=True)
logger = get_logger(__name__)


def build_dataset(macro_overrides: dict | None, n_borrowers: int):
    user_macro = macro_overrides or {}
    required = {"debt_ratio", "delinquency", "interest_rate"}
    missing = list(required - set(user_macro.keys()))

    if missing:
        logger.info(f"Fetching missing macro fields: {missing}")
        fetched = get_macro_data(missing, use_cache=False)
        macro = {**fetched, **user_macro}
    else:
        macro = user_macro

    df = generate_synthetic_data(macro, n=n_borrowers)
    dataset_name = f"dataset_{uuid4().hex[:8]}"
    file_path = DATASET_DIR / f"{dataset_name}.parquet"
    df.to_parquet(file_path, index=False)
    logger.info("Saved dataset %s -> %s", dataset_name, file_path)

    try:
        log_dataset(name=dataset_name, rows=len(df), macro=macro)
    except Exception as e:
        logger.warning("Failed to log dataset to database: %s", e)

    return dataset_name, df, macro
