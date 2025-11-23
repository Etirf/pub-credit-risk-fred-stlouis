"""Integration tests for database operations using PostgreSQL."""
import os
import pytest
import uuid
from datetime import UTC, datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.artifacts.infrastructure.repository import (
    log_dataset,
    log_evaluation,
    log_model,
    log_pruned_model,
)
from app.artifacts.models import (
    Base,
    DatasetRecord,
    EvaluationRecord,
    ModelRecord,
    PrunedModelRecord,
)


POSTGRES_SERVER_URL = os.getenv(
    "POSTGRES_SERVER_URL",
    "postgresql://postgres:postgres@localhost:5432/postgres"
)


def can_connect_to_postgres(url: str) -> bool:
    try:
        engine = create_engine(url, echo=False, connect_args={"connect_timeout": 2})
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        import sys
        error_str = str(e)
        print(f"\n Cannot connect to PostgreSQL at {url}", file=sys.stderr)
        print(f"   Error: {error_str}", file=sys.stderr)
        if "password authentication failed" in error_str.lower():
            print("   Hint: Wrong credentials or local PostgreSQL is intercepting port 5432", file=sys.stderr)
            print("   Fix: Stop local PostgreSQL: sudo systemctl stop postgresql", file=sys.stderr)
            print("   Or: Start Docker PostgreSQL: docker-compose up postgres -d", file=sys.stderr)
        elif "connection refused" in error_str.lower():
            print("   Hint: PostgreSQL server not running on port 5432", file=sys.stderr)
            print("   Fix: Start Docker PostgreSQL: docker-compose up postgres -d", file=sys.stderr)
        else:
            print("   Hint: Check if PostgreSQL is running and credentials are correct", file=sys.stderr)
        return False


@pytest.fixture(scope="session")
def temp_database():
    """Create a temporary PostgreSQL database for testing, drop after all tests complete."""
    if not can_connect_to_postgres(POSTGRES_SERVER_URL):
        pytest.skip(f"PostgreSQL server not accessible at {POSTGRES_SERVER_URL}. Start with: docker-compose up postgres -d")
    
    temp_db_name = f"credit_risk_test_{uuid.uuid4().hex[:8]}"
    admin_engine = create_engine(POSTGRES_SERVER_URL, echo=False, isolation_level="AUTOCOMMIT")
    
    with admin_engine.connect() as conn:
        conn.execute(text(f'CREATE DATABASE "{temp_db_name}"'))
    
    admin_engine.dispose()
    
    # Replace only the database name part in URL
    test_db_url = POSTGRES_SERVER_URL.rsplit("/", 1)[0] + f"/{temp_db_name}"
    
    try:
        yield test_db_url
    finally:
        cleanup_engine = create_engine(POSTGRES_SERVER_URL, echo=False, isolation_level="AUTOCOMMIT")
        
        with cleanup_engine.connect() as conn:
            conn.execute(text(
                f"SELECT pg_terminate_backend(pg_stat_activity.pid) "
                f"FROM pg_stat_activity "
                f"WHERE pg_stat_activity.datname = '{temp_db_name}' "
                f"AND pid <> pg_backend_pid()"
            ))
            conn.execute(text(f'DROP DATABASE IF EXISTS "{temp_db_name}"'))
        
        cleanup_engine.dispose()


@pytest.fixture(scope="function")
def db_session(monkeypatch, temp_database):
    """Create a database session that rolls back after each test."""
    engine = create_engine(temp_database, echo=False)
    Base.metadata.create_all(engine)
    
    connection = engine.connect()
    transaction = connection.begin()
    TestSessionLocal = sessionmaker(bind=connection, autocommit=False, autoflush=False)
    
    from app.artifacts.infrastructure import repository
    import app.artifacts.models.artifacts as models_module
    
    original_session_factory = repository.SessionLocal
    repository.SessionLocal = TestSessionLocal
    
    def test_get_engine():
        return engine
    
    monkeypatch.setattr(models_module, "get_engine", test_get_engine)
    
    def test_get_session():
        return TestSessionLocal()
    
    monkeypatch.setattr(repository, "get_session", test_get_session)
    
    session = TestSessionLocal()
    
    try:
        yield session
    finally:
        if transaction.is_active:
            transaction.rollback()
        session.close()
        connection.close()
        repository.SessionLocal = original_session_factory
        engine.dispose()


def test_log_dataset_creates_record(db_session):
    macro = {"debt_ratio": 0.5, "delinquency": 0.1, "interest_rate": 0.02}
    
    log_dataset(name="dataset_test123", rows=1000, macro=macro)
    
    record = db_session.query(DatasetRecord).filter_by(name="dataset_test123").first()
    assert record is not None
    assert record.name == "dataset_test123"
    assert record.rows == 1000
    assert record.macro == macro
    assert record.created_at is not None


def test_log_model_creates_record_with_foreign_key(db_session):
    macro = {"debt_ratio": 0.5, "delinquency": 0.1, "interest_rate": 0.02}
    log_dataset(name="dataset_test123", rows=1000, macro=macro)
    
    timestamp = datetime.now(UTC)
    log_model(name="model_test456", dataset_name="dataset_test123", timestamp=timestamp)
    
    model_record = db_session.query(ModelRecord).filter_by(name="model_test456").first()
    assert model_record is not None
    assert model_record.name == "model_test456"
    assert model_record.dataset_id is not None
    
    dataset_record = db_session.query(DatasetRecord).filter_by(name="dataset_test123").first()
    assert model_record.dataset_id == dataset_record.id


def test_log_model_fails_if_dataset_not_found(db_session):
    with pytest.raises(ValueError, match="Dataset 'nonexistent' not found"):
        log_model(name="model_test", dataset_name="nonexistent")


def test_log_evaluation_creates_record_with_foreign_keys(db_session):
    macro = {"debt_ratio": 0.5, "delinquency": 0.1, "interest_rate": 0.02}
    log_dataset(name="dataset_test123", rows=1000, macro=macro)
    log_model(name="model_test456", dataset_name="dataset_test123")
    
    log_evaluation(model_name="model_test456", dataset_name="dataset_test123", auc=0.85)
    
    eval_record = db_session.query(EvaluationRecord).first()
    assert eval_record is not None
    assert eval_record.auc == 0.85
    assert eval_record.model_id is not None
    assert eval_record.dataset_id is not None
    
    model_record = db_session.query(ModelRecord).filter_by(name="model_test456").first()
    dataset_record = db_session.query(DatasetRecord).filter_by(name="dataset_test123").first()
    assert eval_record.model_id == model_record.id
    assert eval_record.dataset_id == dataset_record.id


def test_log_evaluation_fails_if_model_not_found(db_session):
    macro = {"debt_ratio": 0.5, "delinquency": 0.1, "interest_rate": 0.02}
    log_dataset(name="dataset_test123", rows=1000, macro=macro)
    
    with pytest.raises(ValueError, match="Model 'nonexistent' not found"):
        log_evaluation(model_name="nonexistent", dataset_name="dataset_test123", auc=0.85)


def test_log_evaluation_fails_if_dataset_not_found(db_session):
    macro = {"debt_ratio": 0.5, "delinquency": 0.1, "interest_rate": 0.02}
    log_dataset(name="dataset_test123", rows=1000, macro=macro)
    log_model(name="model_test456", dataset_name="dataset_test123")
    
    with pytest.raises(ValueError, match="Dataset 'nonexistent' not found"):
        log_evaluation(model_name="model_test456", dataset_name="nonexistent", auc=0.85)


def test_log_pruned_model_creates_record_with_foreign_key(db_session):
    macro = {"debt_ratio": 0.5, "delinquency": 0.1, "interest_rate": 0.02}
    log_dataset(name="dataset_test123", rows=1000, macro=macro)
    log_model(name="model_test456", dataset_name="dataset_test123")
    
    log_pruned_model(model_name="model_test456", pruned_name="model_test456_pruned")
    
    pruned_record = db_session.query(PrunedModelRecord).filter_by(pruned_name="model_test456_pruned").first()
    assert pruned_record is not None
    assert pruned_record.pruned_name == "model_test456_pruned"
    assert pruned_record.base_model_id is not None
    
    model_record = db_session.query(ModelRecord).filter_by(name="model_test456").first()
    assert pruned_record.base_model_id == model_record.id


def test_log_pruned_model_fails_if_base_model_not_found(db_session):
    with pytest.raises(ValueError, match="Model 'nonexistent' not found"):
        log_pruned_model(model_name="nonexistent", pruned_name="pruned_model")


def test_query_by_name_lookup(db_session):
    macro1 = {"debt_ratio": 0.5, "delinquency": 0.1, "interest_rate": 0.02}
    macro2 = {"debt_ratio": 0.6, "delinquency": 0.2, "interest_rate": 0.03}
    
    log_dataset(name="dataset_a", rows=1000, macro=macro1)
    log_dataset(name="dataset_b", rows=2000, macro=macro2)
    
    dataset_a = db_session.query(DatasetRecord).filter_by(name="dataset_a").first()
    dataset_b = db_session.query(DatasetRecord).filter_by(name="dataset_b").first()
    
    assert dataset_a is not None
    assert dataset_a.rows == 1000
    assert dataset_b is not None
    assert dataset_b.rows == 2000
