import pytest
import pandas as pd

from app.evaluate.service import evaluate as evaluate_service


def test_evaluate_workflow_loads_data_and_calls_core(monkeypatch, tmp_path):
    df = pd.DataFrame({"default": [0], "name": ["A"], "feature": [1]})
    dataset_dir = tmp_path / "datasets"
    dataset_dir.mkdir()
    model_dir = tmp_path / "models"
    model_dir.mkdir()
    dataset_name = "heldout_set"
    model_name = "model_v1"
    dataset_path = dataset_dir / f"{dataset_name}.parquet"
    dataset_path.touch()
    model_path = model_dir / f"{model_name}.pkl"
    model_path.touch()

    def fake_read_parquet(path):
        assert path == dataset_path
        return df

    def fake_evaluate_model(dataframe, loaded_model_path):
        assert dataframe is df
        assert loaded_model_path == model_path
        return 0.9

    def fake_log_evaluation(model_name, dataset_name, auc):
        # Mock database call - doesn't actually hit DB
        pass

    monkeypatch.setattr(evaluate_service, "DATASET_DIR", dataset_dir, raising=False)
    monkeypatch.setattr(evaluate_service, "MODEL_DIR", model_dir, raising=False)
    monkeypatch.setattr(evaluate_service.pd, "read_parquet", fake_read_parquet)
    monkeypatch.setattr(evaluate_service, "evaluate_model", fake_evaluate_model)
    monkeypatch.setattr(evaluate_service, "log_evaluation", fake_log_evaluation)

    auc = evaluate_service.evaluate_workflow(model_name, dataset_name)
    assert auc == 0.9


def test_evaluate_workflow_requires_names(monkeypatch, tmp_path):
    dataset_dir = tmp_path / "datasets"
    dataset_dir.mkdir()
    model_dir = tmp_path / "models"
    model_dir.mkdir()
    monkeypatch.setattr(evaluate_service, "DATASET_DIR", dataset_dir, raising=False)
    monkeypatch.setattr(evaluate_service, "MODEL_DIR", model_dir, raising=False)

    with pytest.raises(ValueError):
        evaluate_service.evaluate_workflow(None, "dataset")
