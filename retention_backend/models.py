from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Integer, String
from database import Base


class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    avatar_initial = Column(String(2), nullable=False)
    fcm_token = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Coupon(Base):
    __tablename__ = "coupons"

    coupon_id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, nullable=False, index=True)
    code = Column(String, nullable=False)
    title = Column(String, nullable=False)
    message = Column(String, nullable=False)
    discount_percent = Column(Integer, nullable=False)
    is_used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)


class NotificationLog(Base):
    __tablename__ = "notification_logs"

    log_id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, nullable=False, index=True)
    title = Column(String, nullable=False)
    body = Column(String, nullable=False)
    status = Column(String, default="pending")  # 'pending', 'sent', 'failed'
    sent_at = Column(DateTime, default=datetime.utcnow)
