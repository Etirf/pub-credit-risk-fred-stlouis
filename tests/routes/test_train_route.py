"""Integration tests for /train routes using TestClient."""
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient
from celery.result import AsyncResult

from app.main import app


client = TestClient(app)


class MockAsyncResult(AsyncResult):
    """Mock AsyncResult for testing."""
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
def mock_dataset(tmp_path):
    """Create a temporary dataset file."""
    dataset_dir = tmp_path / "storage" / "datasets"
    dataset_dir.mkdir(parents=True)
    dataset_path = dataset_dir / "dataset_test123.parquet"
    dataset_path.touch()
    return dataset_path


def test_train_endpoint_submits_task(mock_dataset, monkeypatch):
    """Test that /train endpoint submits a Celery task and returns task_id."""
    mock_task_id = "task-abc-123"
    
    mock_async_result = MagicMock()
    mock_async_result.id = mock_task_id
    
    with patch("app.train.routes.train.train_model_task") as mock_task:
        mock_task.delay = MagicMock(return_value=mock_async_result)
        
        with patch("pathlib.Path.exists", return_value=True):
            response = client.post(
                "/train/",
                json={"dataset_name": "dataset_test123"},
            )
            
            assert response.status_code == 200
            payload = response.json()
            assert "task_id" in payload
            assert payload["task_id"] == mock_task_id
            assert payload["status"] == "submitted"
            assert payload["dataset_name"] == "dataset_test123"
            mock_task.delay.assert_called_once_with("dataset_test123")


def test_train_endpoint_returns_404_for_missing_dataset(monkeypatch):
    """Test that /train endpoint returns 404 when dataset doesn't exist."""
    with patch("pathlib.Path.exists") as mock_exists:
        mock_exists.return_value = False
        
        response = client.post(
            "/train/",
            json={"dataset_name": "nonexistent"},
        )
        
        assert response.status_code == 404
        payload = response.json()
        assert "not found" in payload["detail"].lower()


def test_train_status_pending(monkeypatch):
    """Test /train/status endpoint with PENDING state."""
    task_id = "task-abc-123"
    
    # Mock AsyncResult
    with patch("app.train.routes.train.AsyncResult") as mock_async_result:
        mock_result = MockAsyncResult(task_id, state="PENDING")
        mock_async_result.return_value = mock_result
        
        response = client.get(f"/train/status/{task_id}")
        
        assert response.status_code == 200
        payload = response.json()
        assert payload["task_id"] == task_id
        assert payload["status"] == "PENDING"
        assert payload["result"] is None
        assert payload["error"] is None


def test_train_status_success(monkeypatch):
    """Test /train/status endpoint with SUCCESS state."""
    task_id = "task-abc-123"
    task_result = {
        "status": "success",
        "model_name": "model_test456",
        "dataset_name": "dataset_test123",
    }
    
    # Mock AsyncResult
    with patch("app.train.routes.train.AsyncResult") as mock_async_result:
        mock_result = MockAsyncResult(task_id, state="SUCCESS", result=task_result)
        mock_async_result.return_value = mock_result
        
        response = client.get(f"/train/status/{task_id}")
        
        assert response.status_code == 200
        payload = response.json()
        assert payload["task_id"] == task_id
        assert payload["status"] == "SUCCESS"
        assert payload["result"] == task_result
        assert payload["error"] is None


def test_train_status_failure(monkeypatch):
    """Test /train/status endpoint with FAILURE state."""
    task_id = "task-abc-123"
    error_msg = "Dataset not found"
    
    # Mock AsyncResult
    with patch("app.train.routes.train.AsyncResult") as mock_async_result:
        mock_result = MockAsyncResult(task_id, state="FAILURE", info=error_msg)
        mock_async_result.return_value = mock_result
        
        response = client.get(f"/train/status/{task_id}")
        
        assert response.status_code == 200
        payload = response.json()
        assert payload["task_id"] == task_id
        assert payload["status"] == "FAILURE"
        assert payload["error"] == error_msg
        assert payload["result"] is None

