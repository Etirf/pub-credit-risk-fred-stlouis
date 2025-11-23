from fastapi import APIRouter
from app.data.schemas import DatasetRequest, DatasetResponse
from app.data.service import build_dataset
from utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/generate", tags=["Dataset Generation"])


@router.post("/")
def generate_dataset(request: DatasetRequest) -> DatasetResponse:
    """
    Generate a synthetic borrower dataset.
    Optionally override macroeconomic fields in request.
    """
    user_macro = (
        request.macro_overrides.model_dump(exclude_none=True)
        if request.macro_overrides
        else None
    )
    dataset_name, df, macro = build_dataset(user_macro, request.n_borrowers)
    logger.info("Generated dataset %s with shape %s", dataset_name, df.shape)
    preview = df.head(10).to_dict(orient="records")

    return DatasetResponse(
        dataset_name=dataset_name,
        rows=len(df),
        macro=macro,
        preview=preview,
    )
