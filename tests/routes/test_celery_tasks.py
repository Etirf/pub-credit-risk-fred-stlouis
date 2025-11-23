"""Test Celery tasks using .apply() (no Redis needed)."""

from unittest.mock import patch
import pandas as pd

from app.artifacts.service.tasks import (
    train_model_task,
    evaluate_model_task,
    prune_model_task,
)


def test_train_model_task_apply(tmp_path, monkeypatch):
    dataset_dir = tmp_path / "storage" / "datasets"
    model_dir = tmp_path / "storage" / "models"
    dataset_dir.mkdir(parents=True)
    model_dir.mkdir(parents=True)
    
    dataset_path = dataset_dir / "dataset_test123.parquet"
    df = pd.DataFrame({
        "default": [0, 1, 0, 1],
        "name": ["A", "B", "C", "D"],
        "feature1": [1.0, 2.0, 3.0, 4.0],
        "feature2": [0.5, 0.6, 0.7, 0.8],
    })
    df.to_parquet(dataset_path, index=False)
    
    with patch("app.artifacts.service.tasks.train_workflow") as mock_workflow:
        mock_model_path = model_dir / "model_test456.pkl"
        mock_model_path.touch()
        mock_workflow.return_value = mock_model_path
        
        result = train_model_task.apply(args=["dataset_test123"])
        
        assert result.successful()
        task_result = result.result
        assert task_result["status"] == "success"
        assert task_result["dataset_name"] == "dataset_test123"
        assert "model_name" in task_result
        mock_workflow.assert_called_once_with("dataset_test123")


def test_train_model_task_handles_missing_dataset(monkeypatch):
    with patch("app.artifacts.service.tasks.train_workflow") as mock_workflow:
        mock_workflow.side_effect = ValueError("Dataset 'nonexistent' not found")
        
        result = train_model_task.apply(args=["nonexistent"])
        
        assert not result.successful()
        assert isinstance(result.result, ValueError)


def test_evaluate_model_task_apply(tmp_path, monkeypatch):
    dataset_dir = tmp_path / "storage" / "datasets"
    model_dir = tmp_path / "storage" / "models"
    dataset_dir.mkdir(parents=True)
    model_dir.mkdir(parents=True)
    
    with patch("app.artifacts.service.tasks.evaluate_workflow") as mock_workflow:
        mock_workflow.return_value = 0.85
        
        import app.evaluate.service.evaluate as evaluate_service
        
        monkeypatch.setattr(evaluate_service, "DATASET_DIR", dataset_dir)
        monkeypatch.setattr(evaluate_service, "MODEL_DIR", model_dir)
        
        with patch("app.artifacts.infrastructure.repository.log_evaluation"):
            result = evaluate_model_task.apply(args=["model_test456", "dataset_test123"])
            
            assert result.successful()
            task_result = result.result
            assert task_result["status"] == "success"
            assert task_result["model_name"] == "model_test456"
            assert task_result["dataset_name"] == "dataset_test123"
            assert task_result["auc"] == 0.85


def test_prune_model_task_apply(tmp_path, monkeypatch):
    dataset_dir = tmp_path / "storage" / "datasets"
    model_dir = tmp_path / "storage" / "models"
    dataset_dir.mkdir(parents=True)
    model_dir.mkdir(parents=True)
    
    with patch("app.artifacts.service.tasks.prune_workflow") as mock_workflow:
        mock_pruned_path = model_dir / "model_test456_pruned.pkl"
        mock_pruned_path.touch()
        mock_workflow.return_value = mock_pruned_path
        
        import app.prune.service.prune as prune_service
        
        monkeypatch.setattr(prune_service, "DATASET_DIR", dataset_dir)
        monkeypatch.setattr(prune_service, "MODEL_DIR", model_dir)
        
        with patch("app.artifacts.infrastructure.repository.log_pruned_model"):
            result = prune_model_task.apply(args=["model_test456", "dataset_test123"])
            
            assert result.successful()
            task_result = result.result
            assert task_result["status"] == "success"
            assert task_result["model_name"] == "model_test456"
            assert task_result["dataset_name"] == "dataset_test123"
            assert task_result["pruned_model_name"] == "model_test456_pruned"

