# Testing Guide

## Test Categories

### Unit Tests (No Redis/PostgreSQL Required)

Unit tests use mocking and work without Redis or PostgreSQL:

```bash
uv run pytest tests/ -k "not integration"
```

Unit tests include:
- **Route tests** (`tests/routes/`): Test FastAPI endpoints using `TestClient`
  - Mock Celery tasks to return fake `AsyncResult` objects (no Redis needed)
  - Verify HTTP status codes and response JSON matches Pydantic schemas
  - Test all endpoints: `/generate`, `/train`, `/train/status/{task_id}`, `/evaluate`, `/evaluate/status/{task_id}`, `/prune`, `/prune/status/{task_id}`
- **Service tests** (`tests/services/`): Test service layer logic
  - Mock database logging functions (`log_dataset`, `log_model`, etc.) via monkeypatching
  - Mock file operations (parquet read/write)
- **Celery task tests** (`tests/routes/test_celery_tasks.py`): Test Celery tasks directly
  - Use `.apply()` to execute tasks synchronously without Redis
  - Mock workflows to avoid actual ML training/evaluation/pruning
  - Verify task return values and error handling

Unit tests mock:
- Database calls: Monkeypatch `log_dataset`, `log_model`, `log_evaluation`, `log_pruned_model` in service tests
- Celery tasks: Mock `train_model_task.delay()`, `evaluate_model_task.delay()`, `prune_model_task.delay()` in route tests
- ML workflows: Mock `train_workflow`, `evaluate_workflow`, `prune_workflow` in Celery task tests
- File operations: Use temporary directories and mock Path.exists() checks
- External API calls: Mock FRED API calls in service tests

**Note:** Service layer code wraps database calls in try/except blocks that log warnings on failure. Unit tests mock these functions to avoid actual database connections. Route tests mock Celery tasks at the endpoint level, so no Redis or worker is needed.

### Integration Tests (PostgreSQL Required)

Integration tests use a real PostgreSQL database to verify:
- Database schema/models work correctly
- Logging functions persist data correctly
- Foreign key relationships work
- Query lookups by name work

**Prerequisites:**
- PostgreSQL server running (use `docker-compose up postgres -d` or run locally)
- Server accessible at `POSTGRES_SERVER_URL` (defaults to `postgresql://postgres:postgres@localhost:5432/postgres`)

**Note:** Integration tests automatically create a temporary database with a random name, run all tests against it, and drop it when finished. No manual database setup needed!

**Troubleshooting:** If integration tests are skipped or fail with connection errors:

- **Port conflict**: If you have both local PostgreSQL (via systemd) and Docker PostgreSQL running on port 5432, the local one intercepts connections and causes "password authentication failed". Fix: `sudo systemctl stop postgresql` then `docker restart postgres` 

- **Wrong credentials**: Tests use `postgres:postgres@localhost:5432/postgres` by default. Set `POSTGRES_SERVER_URL` environment variable to override.

- **Docker not running**: Start Docker PostgreSQL: `docker-compose up postgres -d`

**Note:** If PostgreSQL server is not accessible, integration tests will be skipped (not fail). This allows unit tests to run without a database. Check test output for skip reasons.

```bash
# Start PostgreSQL (if not already running)
docker-compose up postgres -d

# Run integration tests
uv run pytest tests/integration/

# Or run all tests (unit + integration)
uv run pytest tests/
```

**Note:** Integration tests use PostgreSQL (same as production), ensuring consistency. Each test runs in a transaction that's rolled back, so tests don't interfere with each other.

## Manual Endpoint Testing

### Option 1: Using Docker Compose (Recommended)

This starts PostgreSQL, Redis, API, and Worker all together:

```bash
# Start all services
docker-compose up -d

# Check logs
docker-compose logs -f api

# Stop services
docker-compose down
```

The API will be available at `http://localhost:8000`

### Option 2: Local Testing (API/Worker Without Docker)

This runs the API and worker locally, but still uses Docker's PostgreSQL and Redis:

**Prerequisites:**
- Start Docker services: `docker-compose up postgres redis -d`
- These expose PostgreSQL on `localhost:5432` and Redis on `localhost:6379`

**Start the server:**
```bash
uv run uvicorn app.main:app --reload
```

**Note:** The default `DATABASE_URL` in `settings.py` points to `localhost:5432`, which works with Docker's PostgreSQL service.

### Option 3: Use the Test Script

```bash
# Make sure server is running first
uv run uvicorn app.main:app --reload

# In another terminal, run the test script
./test_endpoints.sh
```

Requires `jq` for JSON formatting: `sudo apt install jq` (or `brew install jq` on Mac)

## Manual Testing with curl

### 1. Generate Dataset

```bash
curl -X POST "http://localhost:8000/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "n_borrowers": 100,
    "macro_overrides": {
      "debt_ratio": 0.5,
      "delinquency": 0.1,
      "interest_rate": 0.02
    }
  }'
```

### 2. Train Model (Async)

```bash
# Submit training job - returns immediately with task_id
curl -X POST "http://localhost:8000/train/" \
  -H "Content-Type: application/json" \
  -d '{
    "dataset_name": "dataset_abc12345"
  }'
# Response: {"task_id": "abc123-def456-ghi789", "status": "submitted", "dataset_name": "dataset_abc12345"}

# Check training status
curl "http://localhost:8000/train/status/{task_id}"
# Response: {"task_id": "abc123-def456-ghi789", "status": "SUCCESS", "result": {"model_name": "model_a1b2c3d4"}}
```

### 3. Evaluate Model (Async)

```bash
# Submit evaluation job - returns immediately with task_id
curl -X POST "http://localhost:8000/evaluate/" \
  -H "Content-Type: application/json" \
  -d '{
    "model_name": "model_abc12345",
    "dataset_name": "dataset_abc12345"
  }'
# Response: {"task_id": "abc123-def456-ghi789", "status": "submitted", "model_name": "model_abc12345", "dataset_name": "dataset_abc12345"}

# Check evaluation status
curl "http://localhost:8000/evaluate/status/{task_id}"
# Response: {"task_id": "abc123-def456-ghi789", "status": "SUCCESS", "result": {"auc": 0.95, "model_name": "model_a1b2c3d4", "dataset_name": "dataset_abc12345"}}
```

### 4. Prune Model (Async)

```bash
# Submit pruning job - returns immediately with task_id
curl -X POST "http://localhost:8000/prune/" \
  -H "Content-Type: application/json" \
  -d '{
    "model_name": "model_abc12345",
    "dataset_name": "dataset_abc12345"
  }'
# Response: {"task_id": "abc123-def456-ghi789", "status": "submitted", "model_name": "model_abc12345", "dataset_name": "dataset_abc12345"}

# Check pruning status
curl "http://localhost:8000/prune/status/{task_id}"
# Response: {"task_id": "abc123-def456-ghi789", "status": "SUCCESS", "result": {"pruned_model_name": "model_a1b2c3d4_pruned", "original_model_name": "model_a1b2c3d4", "dataset_name": "dataset_abc12345"}}
```

## Async Operations

**Training, evaluation, and pruning are async operations** via Celery:

1. Submit a job via POST endpoint -> returns `task_id` immediately
2. Check status via GET `/status/{task_id}` endpoint
3. When status is `SUCCESS`, retrieve results from the `result` field

This matches real MLOps architectures (Kubeflow, MLflow, SageMaker, etc.) where long-running ML operations run asynchronously.

## Testing Without Redis

**Redis is required** for async ML operations (train, evaluate, prune). Without Redis:
- Generate dataset endpoint still works (synchronous)
- Training/evaluation/pruning endpoints will fail (Celery requires Redis)

For local testing without Redis, database logging will still work (database operations are synchronous), but Celery worker tasks require Redis.

## Interactive API Docs

Once the server is running, visit:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

These provide interactive forms to test all endpoints.

