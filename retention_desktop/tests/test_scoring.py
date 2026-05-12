"""Tests for scoring service."""

import pytest
import pandas as pd
import numpy as np

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services.scoring_service import ScoringService
from config import RFM_WEIGHTS


@pytest.fixture
def scoring_service():
    return ScoringService()


def _make_rfm_db(tmp_path, rows):
    """Create a test DB with rfm_scores rows."""
    from sqlalchemy import create_engine, text
    from data.database import Base

    db_path = tmp_path / "test.db"
    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(engine)

    with engine.begin() as conn:
        for r in rows:
            conn.execute(text(
                "INSERT INTO customers (customer_id, country) VALUES (:cid, 'UK')"
            ), {"cid": r["customer_id"]})
            conn.execute(text("""
                INSERT INTO rfm_scores (customer_id, recency, frequency, monetary,
                                        r_score, f_score, m_score, loyalty_score)
                VALUES (:cid, :rec, :freq, :mon, :rs, :fs, :ms, 0)
            """), {
                "cid": r["customer_id"], "rec": 10, "freq": 5, "mon": 100.0,
                "rs": r["r_score"], "fs": r["f_score"], "ms": r["m_score"],
            })

    return engine


def test_scoring_range(scoring_service, tmp_path, monkeypatch):
    """Loyalty scores should be between 0 and 100."""
    import services.scoring_service as mod

    rows = [
        {"customer_id": 1, "r_score": 1, "f_score": 1, "m_score": 1},
        {"customer_id": 2, "r_score": 5, "f_score": 5, "m_score": 5},
        {"customer_id": 3, "r_score": 3, "f_score": 2, "m_score": 4},
    ]
    engine = _make_rfm_db(tmp_path, rows)
    monkeypatch.setattr(mod, "engine", engine)

    result = scoring_service.compute()

    assert (result["loyalty_score"] >= 0).all()
    assert (result["loyalty_score"] <= 100).all()


def test_scoring_extremes(scoring_service, tmp_path, monkeypatch):
    """Min scores (1,1,1) -> 0, Max scores (5,5,5) -> 100."""
    import services.scoring_service as mod

    rows = [
        {"customer_id": 1, "r_score": 1, "f_score": 1, "m_score": 1},
        {"customer_id": 2, "r_score": 5, "f_score": 5, "m_score": 5},
    ]
    engine = _make_rfm_db(tmp_path, rows)
    monkeypatch.setattr(mod, "engine", engine)

    result = scoring_service.compute()
    scores = result.set_index("customer_id")["loyalty_score"]

    assert scores[1] == 0.0, "Min RFM scores should yield loyalty 0"
    assert scores[2] == 100.0, "Max RFM scores should yield loyalty 100"


def test_scoring_different_rfm_yields_different_loyalty(scoring_service, tmp_path, monkeypatch):
    """Different RFM scores should produce different loyalty scores."""
    import services.scoring_service as mod

    rows = [
        {"customer_id": 1, "r_score": 1, "f_score": 1, "m_score": 1},
        {"customer_id": 2, "r_score": 3, "f_score": 3, "m_score": 3},
        {"customer_id": 3, "r_score": 5, "f_score": 5, "m_score": 5},
    ]
    engine = _make_rfm_db(tmp_path, rows)
    monkeypatch.setattr(mod, "engine", engine)

    result = scoring_service.compute()
    scores = result["loyalty_score"].tolist()

    assert len(set(scores)) == 3, "Three different RFM combos should yield 3 different loyalty scores"


def test_scoring_formula_correctness(scoring_service, tmp_path, monkeypatch):
    """Verify the weighted formula produces expected values."""
    import services.scoring_service as mod

    rows = [{"customer_id": 1, "r_score": 2, "f_score": 4, "m_score": 3}]
    engine = _make_rfm_db(tmp_path, rows)
    monkeypatch.setattr(mod, "engine", engine)

    result = scoring_service.compute()
    actual = result.iloc[0]["loyalty_score"]

    w_r = RFM_WEIGHTS["recency"]
    w_f = RFM_WEIGHTS["frequency"]
    w_m = RFM_WEIGHTS["monetary"]
    raw = 2 * w_r + 4 * w_f + 3 * w_m
    min_p = 1.0 * (w_r + w_f + w_m)
    max_p = 5.0 * (w_r + w_f + w_m)
    expected = round((raw - min_p) / (max_p - min_p) * 100, 2)

    assert actual == expected, f"Expected {expected}, got {actual}"


def test_scoring_empty_db(scoring_service, tmp_path, monkeypatch):
    """Should return empty DataFrame for empty database."""
    from sqlalchemy import create_engine
    from data.database import Base
    import services.scoring_service as mod

    engine = create_engine(f"sqlite:///{tmp_path / 'empty.db'}")
    Base.metadata.create_all(engine)
    monkeypatch.setattr(mod, "engine", engine)

    result = scoring_service.compute()
    assert result.empty
