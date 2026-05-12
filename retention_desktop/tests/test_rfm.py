"""Tests for RFM service."""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services.rfm_service import RFMService
from config import RFM_SCORE_BINS


@pytest.fixture
def rfm_service():
    return RFMService()


@pytest.fixture
def sample_transactions(tmp_path):
    """Create a temporary SQLite DB with sample transactions."""
    from sqlalchemy import create_engine, text
    from data.database import Base

    db_path = tmp_path / "test.db"
    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(engine)

    with engine.begin() as conn:
        # Insert 20 customers
        for cid in range(1, 21):
            conn.execute(text(
                "INSERT INTO customers (customer_id, country) VALUES (:cid, 'UK')"
            ), {"cid": cid})

        # Insert transactions with varying dates and amounts
        base_date = datetime(2024, 12, 1)
        for cid in range(1, 21):
            for order in range(1, cid + 1):  # customer N has N orders
                conn.execute(text("""
                    INSERT INTO transactions (invoice_no, customer_id, stock_code,
                                              description, quantity, price, invoice_date)
                    VALUES (:inv, :cid, 'A001', 'Item', :qty, :price, :date)
                """), {
                    "inv": f"INV{cid:03d}_{order}",
                    "cid": cid,
                    "qty": order,
                    "price": 10.0 + cid,
                    "date": datetime(2024, 12, 1, 10, 0) if order == 1
                    else datetime(2024, 11, 1 + cid, 10, 0),
                })

    return engine


def test_rfm_compute_returns_dataframe(rfm_service, sample_transactions, monkeypatch):
    """RFM compute should return a DataFrame with expected columns."""
    import services.rfm_service as mod
    monkeypatch.setattr(mod, "engine", sample_transactions)

    ref_date = datetime(2025, 1, 1)
    result = rfm_service.compute(reference_date=ref_date)

    assert isinstance(result, pd.DataFrame)
    assert not result.empty
    expected_cols = {"customer_id", "recency", "frequency", "monetary",
                     "r_score", "f_score", "m_score"}
    assert expected_cols.issubset(set(result.columns))


def test_rfm_scores_range(rfm_service, sample_transactions, monkeypatch):
    """All RFM scores should be between 1 and RFM_SCORE_BINS."""
    import services.rfm_service as mod
    monkeypatch.setattr(mod, "engine", sample_transactions)

    result = rfm_service.compute(reference_date=datetime(2025, 1, 1))

    for col in ["r_score", "f_score", "m_score"]:
        assert result[col].min() >= 1, f"{col} min should be >= 1"
        assert result[col].max() <= RFM_SCORE_BINS, f"{col} max should be <= {RFM_SCORE_BINS}"


def test_rfm_scores_distribution(rfm_service, sample_transactions, monkeypatch):
    """Scores should be distributed across bins (not all the same)."""
    import services.rfm_service as mod
    monkeypatch.setattr(mod, "engine", sample_transactions)

    result = rfm_service.compute(reference_date=datetime(2025, 1, 1))

    for col in ["r_score", "f_score", "m_score"]:
        unique_scores = result[col].nunique()
        assert unique_scores > 1, f"{col} should have multiple distinct values, got {unique_scores}"


def test_rfm_recency_positive(rfm_service, sample_transactions, monkeypatch):
    """Recency should always be positive."""
    import services.rfm_service as mod
    monkeypatch.setattr(mod, "engine", sample_transactions)

    result = rfm_service.compute(reference_date=datetime(2025, 1, 1))
    assert (result["recency"] > 0).all()


def test_rfm_monetary_non_negative(rfm_service, sample_transactions, monkeypatch):
    """Monetary should be non-negative."""
    import services.rfm_service as mod
    monkeypatch.setattr(mod, "engine", sample_transactions)

    result = rfm_service.compute(reference_date=datetime(2025, 1, 1))
    assert (result["monetary"] >= 0).all()


def test_rfm_empty_db(rfm_service, tmp_path, monkeypatch):
    """Should return empty DataFrame for empty database."""
    from sqlalchemy import create_engine
    from data.database import Base
    import services.rfm_service as mod

    engine = create_engine(f"sqlite:///{tmp_path / 'empty.db'}")
    Base.metadata.create_all(engine)
    monkeypatch.setattr(mod, "engine", engine)

    result = rfm_service.compute()
    assert result.empty
