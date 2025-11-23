import pandas as pd

from app.data.service import generate as generate_service


def test_build_dataset_persists_named_dataset(monkeypatch, tmp_path):
    calls = {}
    dataset_dir = tmp_path / "datasets"
    dataset_dir.mkdir()

    def fake_get_macro_data(fields, use_cache):
        calls["fields"] = fields
        return {field: 0.1 for field in fields}

    def fake_generate_synthetic_data(macro, n):
        calls["macro"] = macro
        calls["n"] = n
        return pd.DataFrame({"id": [1, 2]})

    def fake_uuid():
        return type("U", (), {"hex": "deadbeefcafebabe"})()

    def fake_log_dataset(name, rows, macro):
        # Mock database call - doesn't actually hit DB
        calls["logged_dataset"] = name

    writes = {}

    def fake_to_parquet(self, path, index=False):
        writes["path"] = path
        writes["index"] = index

    monkeypatch.setattr(generate_service, "DATASET_DIR", dataset_dir, raising=False)
    monkeypatch.setattr(generate_service, "get_macro_data", fake_get_macro_data)
    monkeypatch.setattr(generate_service, "generate_synthetic_data", fake_generate_synthetic_data)
    monkeypatch.setattr(generate_service, "uuid4", fake_uuid)
    monkeypatch.setattr(generate_service, "log_dataset", fake_log_dataset)
    monkeypatch.setattr(pd.DataFrame, "to_parquet", fake_to_parquet, raising=False)

    dataset_name, df, macro = generate_service.build_dataset({"debt_ratio": 0.5}, 5)

    assert dataset_name == "dataset_deadbeef"
    assert writes["path"] == dataset_dir / "dataset_deadbeef.parquet"
    assert writes["index"] is False
    assert set(calls["fields"]) == {"delinquency", "interest_rate"}
    assert calls["n"] == 5
    assert df.equals(pd.DataFrame({"id": [1, 2]}))
    assert macro["debt_ratio"] == 0.5
    assert set(macro.keys()) == {"debt_ratio", "delinquency", "interest_rate"}
    assert calls["logged_dataset"] == "dataset_deadbeef"
