"""Integration tests for /evaluate routes using TestClient."""
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient
from celery.result import AsyncResult

from app.main import app


client = TestClient(app)


class MockAsyncResult(AsyncResult):
    def __init__(self, task_id: str, state: str = "PENDING", result: dict | None = None, info: str | None = None):
        self.id = task_id
        self._state = state
        self._result = result
        self._info = info
    
    @property
    def state(self):
        return self._state
    
    @property
    def result(self):
        return self._result
    
    @property
    def info(self):
        return self._info


@pytest.fixture
def mock_artifacts(tmp_path):
    model_dir = tmp_path / "storage" / "models"
    dataset_dir = tmp_path / "storage" / "datasets"
    model_dir.mkdir(parents=True)
    dataset_dir.mkdir(parents=True)
    
    model_path = model_dir / "model_test456.pkl"
    dataset_path = dataset_dir / "dataset_test123.parquet"
    model_path.touch()
    dataset_path.touch()
    
    return model_path, dataset_path


def test_evaluate_endpoint_submits_task(mock_artifacts, monkeypatch):
    """Test that /evaluate endpoint submits a Celery task and returns task_id."""
    model_path, dataset_path = mock_artifacts
    mock_task_id = "task-eval-123"
    
    
    mock_async_result = MagicMock()
    mock_async_result.id = mock_task_id # Mock the Celery task to return a fake AsyncResult
    
   
    with patch("app.evaluate.routes.evaluate.evaluate_model_task") as mock_task:
        mock_task.delay = MagicMock(return_value=mock_async_result)  # Mock the task's delay method
        
        
        from pathlib import Path as PathClass
        original_exists = PathClass.exists # Mock Path.exists to return True for the artifact checks
        
        def mock_exists(self):
            # Only mock for our test artifacts
            if str(self).endswith("model_test456.pkl") or str(self).endswith("dataset_test123.parquet"):
                return True
            return original_exists(self)
        
        monkeypatch.setattr(PathClass, "exists", mock_exists)
        
        try:
            response = client.post(
                "/evaluate/",
                json={
                    "model_name": "model_test456",
                    "dataset_name": "dataset_test123",
                },
            )
            
            assert response.status_code == 200
            payload = response.json()
            assert payload["task_id"] == mock_task_id
            assert payload["status"] == "submitted"
            assert payload["model_name"] == "model_test456"
            assert payload["dataset_name"] == "dataset_test123"
            
            # Verify task was called
            mock_task.delay.assert_called_once_with("model_test456", "dataset_test123")
        finally:
            monkeypatch.undo()


def test_evaluate_endpoint_returns_404_for_missing_model(monkeypatch):
    """Test that /evaluate endpoint returns 404 when model doesn't exist."""
    from app.evaluate.routes import evaluate as evaluate_module
    from pathlib import Path
    
    mock_model_path = MagicMock(spec=Path)
    mock_model_path.exists.return_value = False
    
    mock_dataset_path = MagicMock(spec=Path)
    mock_dataset_path.exists.return_value = True
    
    monkeypatch.setattr(evaluate_module, "MODEL_DIR", MagicMock(__truediv__=lambda self, other: mock_model_path if other == "nonexistent.pkl" else mock_model_path))
    monkeypatch.setattr(evaluate_module, "DATASET_DIR", MagicMock(__truediv__=lambda self, other: mock_dataset_path))
    
    response = client.post(
        "/evaluate/",
        json={
            "model_name": "nonexistent",
            "dataset_name": "dataset_test123",
        },
    )
    
    assert response.status_code == 404
    payload = response.json()
    assert "not found" in payload["detail"].lower()


def test_evaluate_status_success(monkeypatch):
    task_id = "task-eval-123"
    task_result = {
        "status": "success",
        "model_name": "model_test456",
        "dataset_name": "dataset_test123",
        "auc": 0.85,
    }
    
    with patch("app.evaluate.routes.evaluate.AsyncResult") as mock_async_result:
        mock_result = MockAsyncResult(task_id, state="SUCCESS", result=task_result)
        mock_async_result.return_value = mock_result
        
        response = client.get(f"/evaluate/status/{task_id}")
        
        assert response.status_code == 200
        payload = response.json()
        assert payload["task_id"] == task_id
        assert payload["status"] == "SUCCESS"
        assert payload["result"] == task_result
        assert payload["result"]["auc"] == 0.85

