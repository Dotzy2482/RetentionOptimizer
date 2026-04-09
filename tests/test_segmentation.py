"""Tests for segmentation service."""

import pytest
import pandas as pd
import numpy as np

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services.segmentation_service import SegmentationService
from config import N_CLUSTERS, SEGMENT_LABELS


@pytest.fixture
def seg_service():
    return SegmentationService()


def _make_rfm_db(tmp_path, n=100):
    """Create a test DB with n customers having varied RFM values."""
    from sqlalchemy import create_engine, text
    from data.database import Base

    db_path = tmp_path / "test.db"
    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(engine)

    rng = np.random.RandomState(42)

    with engine.begin() as conn:
        for cid in range(1, n + 1):
            conn.execute(text(
                "INSERT INTO customers (customer_id, country) VALUES (:cid, 'UK')"
            ), {"cid": cid})

            recency = int(rng.exponential(scale=100)) + 1
            frequency = int(rng.poisson(lam=5)) + 1
            monetary = round(float(rng.lognormal(mean=5, sigma=1)), 2)
            r_score = int(rng.randint(1, 6))
            f_score = int(rng.randint(1, 6))
            m_score = int(rng.randint(1, 6))

            conn.execute(text("""
                INSERT INTO rfm_scores (customer_id, recency, frequency, monetary,
                                        r_score, f_score, m_score, loyalty_score)
                VALUES (:cid, :rec, :freq, :mon, :rs, :fs, :ms, 50.0)
            """), {
                "cid": cid, "rec": recency, "freq": frequency, "mon": monetary,
                "rs": r_score, "fs": f_score, "ms": m_score,
            })

    return engine


def test_segmentation_returns_correct_columns(seg_service, tmp_path, monkeypatch):
    """Compute should return DataFrame with customer_id and segment_label."""
    import services.segmentation_service as mod
    engine = _make_rfm_db(tmp_path)
    monkeypatch.setattr(mod, "engine", engine)

    result = seg_service.compute()

    assert isinstance(result, pd.DataFrame)
    assert "customer_id" in result.columns
    assert "segment_label" in result.columns


def test_segmentation_produces_n_clusters(seg_service, tmp_path, monkeypatch):
    """Should produce exactly N_CLUSTERS distinct segments."""
    import services.segmentation_service as mod
    engine = _make_rfm_db(tmp_path, n=200)
    monkeypatch.setattr(mod, "engine", engine)

    result = seg_service.compute()
    unique_segments = result["segment_label"].nunique()

    assert unique_segments == N_CLUSTERS, \
        f"Expected {N_CLUSTERS} segments, got {unique_segments}"


def test_segmentation_uses_valid_labels(seg_service, tmp_path, monkeypatch):
    """All segment labels should be from SEGMENT_LABELS config."""
    import services.segmentation_service as mod
    engine = _make_rfm_db(tmp_path)
    monkeypatch.setattr(mod, "engine", engine)

    result = seg_service.compute()
    valid_labels = set(SEGMENT_LABELS.values())
    actual_labels = set(result["segment_label"].unique())

    assert actual_labels.issubset(valid_labels), \
        f"Unexpected labels: {actual_labels - valid_labels}"


def test_segmentation_all_customers_assigned(seg_service, tmp_path, monkeypatch):
    """Every customer should be assigned to a segment."""
    import services.segmentation_service as mod
    n = 80
    engine = _make_rfm_db(tmp_path, n=n)
    monkeypatch.setattr(mod, "engine", engine)

    result = seg_service.compute()

    assert len(result) == n, f"Expected {n} rows, got {len(result)}"
    assert result["segment_label"].isna().sum() == 0, "No customer should have null segment"


def test_segmentation_empty_db(seg_service, tmp_path, monkeypatch):
    """Should return empty DataFrame for empty database."""
    from sqlalchemy import create_engine
    from data.database import Base
    import services.segmentation_service as mod

    engine = create_engine(f"sqlite:///{tmp_path / 'empty.db'}")
    Base.metadata.create_all(engine)
    monkeypatch.setattr(mod, "engine", engine)

    result = seg_service.compute()
    assert result.empty


def test_segmentation_deterministic(seg_service, tmp_path, monkeypatch):
    """Running segmentation twice on the same data should give the same result."""
    import services.segmentation_service as mod
    engine = _make_rfm_db(tmp_path)
    monkeypatch.setattr(mod, "engine", engine)

    result1 = seg_service.compute()
    result2 = seg_service.compute()

    pd.testing.assert_frame_equal(result1, result2)
