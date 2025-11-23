from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, JSON, create_engine
from sqlalchemy.orm import DeclarativeBase, relationship, sessionmaker

from settings import settings


class Base(DeclarativeBase):
    pass


class DatasetRecord(Base):
    """Dataset artifact metadata."""
    __tablename__ = "datasets"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False, index=True)
    rows = Column(Integer, nullable=False)
    macro = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)

    models = relationship("ModelRecord", back_populates="dataset")
    evaluations = relationship("EvaluationRecord", back_populates="dataset")


class ModelRecord(Base):
    """Model artifact metadata."""
    __tablename__ = "models"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False, index=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)

    dataset = relationship("DatasetRecord", back_populates="models")
    evaluations = relationship("EvaluationRecord", back_populates="model")
    pruned_models = relationship("PrunedModelRecord", back_populates="base_model")


class EvaluationRecord(Base):
    """Model evaluation metadata."""
    __tablename__ = "evaluations"

    id = Column(Integer, primary_key=True)
    model_id = Column(Integer, ForeignKey("models.id"), nullable=False, index=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=False, index=True)
    auc = Column(Float, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)

    model = relationship("ModelRecord", back_populates="evaluations")
    dataset = relationship("DatasetRecord", back_populates="evaluations")


class PrunedModelRecord(Base):
    """Pruned model artifact metadata."""
    __tablename__ = "pruned_models"

    id = Column(Integer, primary_key=True)
    pruned_name = Column(String, unique=True, nullable=False, index=True)
    base_model_id = Column(Integer, ForeignKey("models.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)

    base_model = relationship("ModelRecord", back_populates="pruned_models")


def get_engine():
    """Create SQLAlchemy engine."""
    from pathlib import Path

    db_url = getattr(settings, "database_url", "postgresql://postgres:postgres@localhost:5432/credit_risk")
    
    if db_url.startswith("sqlite"):
        db_path = Path(db_url.replace("sqlite:///", ""))
        db_path.parent.mkdir(parents=True, exist_ok=True)
    
    return create_engine(db_url, echo=False)


def get_session_factory():
    """Create session factory."""
    engine = get_engine()
    return sessionmaker(bind=engine)


def init_db():
    """Initialize database tables."""
    engine = get_engine()
    Base.metadata.create_all(engine)

