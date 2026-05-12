from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional


# === Auth ===
class LoginRequest(BaseModel):
    customer_id: int

class LoginResponse(BaseModel):
    user_id: int
    customer_id: int
    name: str
    email: str
    avatar_initial: str
    loyalty_score: float
    segment: str


# === User Profile ===
class UserProfile(BaseModel):
    user_id: int
    customer_id: int
    name: str
    email: str
    avatar_initial: str
    loyalty_score: float
    segment: str
    recency: int
    frequency: int
    monetary: float
    churn_probability: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


# === Coupons ===
class CouponResponse(BaseModel):
    coupon_id: int
    customer_id: int
    code: str
    title: str
    message: str
    discount_percent: int
    is_used: bool
    created_at: datetime
    expires_at: datetime

    model_config = ConfigDict(from_attributes=True)


# === Admin Send Coupon ===
class SendCouponRequest(BaseModel):
    segment: str
    title: str
    message: str
    discount_percent: int
    days_valid: int = 7
    code_prefix: str = "PROMO"

class SendCouponResponse(BaseModel):
    success: bool
    affected_users: int
    coupon_codes: list[str]
    message: str


# === FCM Token Update ===
class FcmTokenRequest(BaseModel):
    customer_id: int
    fcm_token: str
