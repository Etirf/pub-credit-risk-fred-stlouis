from pathlib import Path
import pickle
from utils.logger import get_logger

logger = get_logger(__name__)

def load_cache(path: Path) -> dict:
    """Load a single-series cache file."""
    if path.exists():
        try:
            with open(path, "rb") as f:
                return pickle.load(f)
        except Exception as e:
            logger.warning(f"Failed to load cache {path.name}: {e}")
    return {}


def save_cache(path: Path, data: dict):
    """Atomically write a cache file."""
    path.parent.mkdir(exist_ok=True)
    tmp = path.with_suffix(".tmp")
    with open(tmp, "wb") as f:
        pickle.dump(data, f)
    tmp.replace(path)