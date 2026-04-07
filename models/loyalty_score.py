from dataclasses import dataclass


@dataclass
class LoyaltyScoreDTO:
    """Data transfer object for RFM-based loyalty scores."""
    customer_id: int
    recency: int
    frequency: int
    monetary: float
    r_score: int
    f_score: int
    m_score: int
    loyalty_score: float
