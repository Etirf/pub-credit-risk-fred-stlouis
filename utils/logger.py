import logging
from pathlib import Path
import pandas as pd

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

def get_logger(name: str) -> logging.Logger:
    """Return a standardized logger for any module."""
    log_path = LOG_DIR / "pipeline.log"

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.FileHandler(log_path, mode="a", encoding="utf-8"),
            logging.StreamHandler()
        ],
    )
    return logging.getLogger(name)



def log_dataframe_preview(df: pd.DataFrame, logger: logging.Logger, name: str, max_rows: int = 100) -> None:
    """Logs DataFrame shape + saves a small readable CSV preview."""
    preview_path = LOG_DIR / f"{name}_preview.csv"
    df.head(max_rows).to_csv(preview_path, index=False)
    logger.info(f"Logged preview for {name}: {df.shape} -> {preview_path}")
    