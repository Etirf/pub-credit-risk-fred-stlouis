import pytest

import pandas as pd

from app.train.service import train as train_service


def test_train_workflow_uses_named_dataset(monkeypatch, tmp_path):
    df = pd.DataFrame({"default": [0], "name": ["A"], "feature": [1]})
    dataset_dir = tmp_path / "datasets"
    dataset_dir.mkdir()
    model_dir = tmp_path / "models"
    model_dir.mkdir()
    dataset_name = "training_data"
    dataset_path = dataset_dir / f"{dataset_name}.parquet"
    dataset_path.touch()

    logged_models = {}

    def fake_read_parquet(path):
        assert path == dataset_path
        return df

    def fake_train_model(dataframe, output_dir):
        assert dataframe is df
        assert output_dir == model_dir
        return model_dir / "model_final.pkl"

    def fake_log_model(name, dataset_name, timestamp=None):
        # Mock database call - doesn't actually hit DB
        logged_models[name] = dataset_name

    monkeypatch.setattr(train_service, "DATASET_DIR", dataset_dir, raising=False)
    monkeypatch.setattr(train_service, "MODEL_DIR", model_dir, raising=False)
    monkeypatch.setattr(train_service.pd, "read_parquet", fake_read_parquet)
    monkeypatch.setattr(train_service, "train_model", fake_train_model)
    monkeypatch.setattr(train_service, "log_model", fake_log_model)

    result = train_service.train_workflow(dataset_name)
    assert result == model_dir / "model_final.pkl"
    assert "model_final" in logged_models
    assert logged_models["model_final"] == dataset_name


def test_train_workflow_requires_existing_dataset(monkeypatch, tmp_path):
    dataset_dir = tmp_path / "datasets"
    dataset_dir.mkdir()
    monkeypatch.setattr(train_service, "DATASET_DIR", dataset_dir, raising=False)
    with pytest.raises(ValueError):
        train_service.train_workflow("missing_dataset")
