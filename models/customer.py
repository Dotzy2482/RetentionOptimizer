from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class CustomerDTO:
    """Data transfer object for customer data used in the UI layer."""
    customer_id: int
    country: str
    first_purchase_date: datetime
    last_purchase_date: datetime
    total_transactions: int = 0
    total_spent: float = 0.0
    segment_label: Optional[str] = None
    loyalty_score: Optional[float] = None
    churn_probability: Optional[float] = None
