import pytest

import pandas as pd

from app.prune.service import prune as prune_service


def test_prune_workflow_loads_data_and_calls_core(monkeypatch, tmp_path):
    df = pd.DataFrame({"default": [0], "name": ["A"], "feature": [1]})
    dataset_dir = tmp_path / "datasets"
    dataset_dir.mkdir()
    model_dir = tmp_path / "models"
    model_dir.mkdir()
    dataset_name = "prune_dataset"
    model_name = "model_v1"
    dataset_path = dataset_dir / f"{dataset_name}.parquet"
    dataset_path.touch()
    model_path = model_dir / f"{model_name}.pkl"
    model_path.touch()

    def fake_read_parquet(path):
        assert path == dataset_path
        return df

    def fake_prune_model(dataframe, loaded_model_path):
        assert dataframe is df
        assert loaded_model_path == model_path
        return model_dir / "model_v1_pruned.pkl"

    def fake_log_pruned_model(model_name, pruned_name):
        # Mock database call - doesn't actually hit DB
        pass

    monkeypatch.setattr(prune_service, "DATASET_DIR", dataset_dir, raising=False)
    monkeypatch.setattr(prune_service, "MODEL_DIR", model_dir, raising=False)
    monkeypatch.setattr(prune_service.pd, "read_parquet", fake_read_parquet)
    monkeypatch.setattr(prune_service, "prune_model", fake_prune_model)
    monkeypatch.setattr(prune_service, "log_pruned_model", fake_log_pruned_model)

    pruned_path = prune_service.prune_workflow(model_name, dataset_name)
    assert pruned_path == model_dir / "model_v1_pruned.pkl"


def test_prune_workflow_requires_inputs(monkeypatch, tmp_path):
    dataset_dir = tmp_path / "datasets"
    dataset_dir.mkdir()
    model_dir = tmp_path / "models"
    model_dir.mkdir()
    monkeypatch.setattr(prune_service, "DATASET_DIR", dataset_dir, raising=False)
    monkeypatch.setattr(prune_service, "MODEL_DIR", model_dir, raising=False)

    with pytest.raises(ValueError):
        prune_service.prune_workflow(None, "dataset")
