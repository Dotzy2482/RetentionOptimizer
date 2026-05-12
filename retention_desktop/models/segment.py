from dataclasses import dataclass


@dataclass
class SegmentDTO:
    """Data transfer object for customer segments."""
    label: str
    count: int
    avg_recency: float
    avg_frequency: float
    avg_monetary: float
    avg_loyalty_score: float
    churn_rate: float
