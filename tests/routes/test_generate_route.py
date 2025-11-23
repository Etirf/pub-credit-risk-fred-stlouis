import pandas as pd
from fastapi.testclient import TestClient

from app.main import app
from app.data.routes import generate as generate_module


client = TestClient(app)


def test_generate_route_returns_preview(monkeypatch):
    def fake_build_dataset(macro_overrides, n_borrowers):
        df = pd.DataFrame({"id": [1, 2, 3]})
        macro = {
            "debt_ratio": 0.5,
            "delinquency": 0.1,
            "interest_rate": 0.2,
        }
        return "dataset_1234", df, macro

    monkeypatch.setattr(generate_module, "build_dataset", fake_build_dataset)

    response = client.post(
        "/generate/",
        json={
            "n_borrowers": 3,
            "macro_overrides": {
                "debt_ratio": 0.4,
            },
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["dataset_name"] == "dataset_1234"
    assert payload["rows"] == 3
    assert payload["macro"] == {
        "debt_ratio": 0.5,
        "delinquency": 0.1,
        "interest_rate": 0.2,
    }
    assert payload["preview"] == [{"id": 1}, {"id": 2}, {"id": 3}]
