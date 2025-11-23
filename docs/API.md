# API Documentation

## Error Handling

- **400 Bad Request**: Invalid request payload or malformed input
- **404 Not Found**: Referenced artifact (dataset/model) does not exist
- **500 Internal Server Error**: Server-side errors (data corruption, unreadable artifacts)

Invalid artifact names (non-existent datasets/models) result in **404 Not Found** responses.

## Endpoints

### Generate Dataset
```http
POST /generate
Content-Type: application/json

{
  "n_borrowers": 1000,
  "macro_overrides": {
    "debt_ratio": 0.5,
    "delinquency": 0.1,
    "interest_rate": 0.2
  }
}
```

Response:
```json
{
  "dataset_name": "dataset_a1b2c3d4",
  "rows": 1000,
  "macro": {
    "debt_ratio": 0.5,
    "delinquency": 0.1,
    "interest_rate": 0.2
  },
  "preview": [
    {"feature1": 1.0, "feature2": 2.0, "default": 0},
    {"feature1": 1.5, "feature2": 2.5, "default": 1}
  ]
}
```

The preview field contains the first 10 rows of the generated dataset.

### Train Model (Async)
```http
POST /train/
Content-Type: application/json

{
  "dataset_name": "dataset_a1b2c3d4"
}
```

Response (immediate):
```json
{
  "task_id": "abc123-def456-ghi789-jkl012-mno345",
  "status": "submitted",
  "dataset_name": "dataset_a1b2c3d4"
}
```

Check status:
```http
GET /train/status/{task_id}
```

Status response:
```json
{
  "task_id": "abc123-def456-ghi789-jkl012-mno345",
  "status": "SUCCESS",
  "result": {
    "status": "success",
    "model_name": "model_a1b2c3d4",
    "dataset_name": "dataset_a1b2c3d4"
  }
}
```

**Note:** Training, evaluation, and pruning are async operations. Endpoints return immediately with a `task_id`. Use status endpoints to check progress.

### Evaluate Model (Async)
```http
POST /evaluate/
Content-Type: application/json

{
  "model_name": "model_a1b2c3d4",
  "dataset_name": "dataset_a1b2c3d4"
}
```

Response (immediate):
```json
{
  "task_id": "abc123-def456-ghi789-jkl012-mno345",
  "status": "submitted",
  "model_name": "model_a1b2c3d4",
  "dataset_name": "dataset_a1b2c3d4"
}
```

Check status:
```http
GET /evaluate/status/{task_id}
```

Status response:
```json
{
  "task_id": "abc123-def456-ghi789-jkl012-mno345",
  "status": "SUCCESS",
  "result": {
    "status": "success",
    "model_name": "model_a1b2c3d4",
    "dataset_name": "dataset_a1b2c3d4",
    "auc": 0.85
  }
}
```

### Prune Model (Async)
```http
POST /prune/
Content-Type: application/json

{
  "model_name": "model_a1b2c3d4",
  "dataset_name": "dataset_a1b2c3d4"
}
```

Response (immediate):
```json
{
  "task_id": "abc123-def456-ghi789-jkl012-mno345",
  "status": "submitted",
  "model_name": "model_a1b2c3d4",
  "dataset_name": "dataset_a1b2c3d4"
}
```

Check status:
```http
GET /prune/status/{task_id}
```

Status response:
```json
{
  "task_id": "abc123-def456-ghi789-jkl012-mno345",
  "status": "SUCCESS",
  "result": {
    "status": "success",
    "model_name": "model_a1b2c3d4",
    "pruned_model_name": "model_a1b2c3d4_pruned",
    "dataset_name": "dataset_a1b2c3d4"
  }
}
```

Uses `sklearn.feature_selection.SelectFromModel` with `threshold="mean"` based on model coefficients.

