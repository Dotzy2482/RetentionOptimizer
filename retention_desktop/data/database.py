from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    Float,
    String,
    DateTime,
    ForeignKey,
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

from config import DB_URL

engine = create_engine(DB_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class Customer(Base):
    __tablename__ = "customers"

    customer_id = Column(Integer, primary_key=True)
    country = Column(String, nullable=True)
    first_purchase_date = Column(DateTime, nullable=True)
    last_purchase_date = Column(DateTime, nullable=True)

    transactions = relationship("Transaction", back_populates="customer")
    rfm_score = relationship("RFMScore", back_populates="customer", uselist=False)
    segment = relationship("Segment", back_populates="customer", uselist=False)


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    invoice_no = Column(String, nullable=False, index=True)
    customer_id = Column(Integer, ForeignKey("customers.customer_id"), nullable=False, index=True)
    stock_code = Column(String, nullable=False)
    description = Column(String, nullable=True)
    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    invoice_date = Column(DateTime, nullable=False)

    customer = relationship("Customer", back_populates="transactions")


class RFMScore(Base):
    __tablename__ = "rfm_scores"

    customer_id = Column(Integer, ForeignKey("customers.customer_id"), primary_key=True)
    recency = Column(Integer, nullable=False)
    frequency = Column(Integer, nullable=False)
    monetary = Column(Float, nullable=False)
    r_score = Column(Integer, nullable=False)
    f_score = Column(Integer, nullable=False)
    m_score = Column(Integer, nullable=False)
    loyalty_score = Column(Float, nullable=False)

    customer = relationship("Customer", back_populates="rfm_score")


class Segment(Base):
    __tablename__ = "segments"

    customer_id = Column(Integer, ForeignKey("customers.customer_id"), primary_key=True)
    segment_label = Column(String, nullable=False)
    churn_probability = Column(Float, nullable=True)
    prediction_date = Column(DateTime, nullable=True)

    customer = relationship("Customer", back_populates="segment")


def init_db():
    """Create all tables if they don't exist."""
    Base.metadata.create_all(engine)


def get_session():
    """Return a new database session."""
    return SessionLocal()
