from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from data.database import Customer, Transaction, RFMScore, Segment, get_session


class CustomerRepository:
    def __init__(self, session: Optional[Session] = None):
        self.session = session or get_session()

    def get_all(self) -> list[Customer]:
        return self.session.query(Customer).all()

    def get_by_id(self, customer_id: int) -> Optional[Customer]:
        return self.session.query(Customer).filter_by(customer_id=customer_id).first()

    def upsert(self, customer_id: int, country: str,
               first_purchase: datetime, last_purchase: datetime) -> Customer:
        customer = self.get_by_id(customer_id)
        if customer:
            customer.country = country
            if first_purchase < customer.first_purchase_date:
                customer.first_purchase_date = first_purchase
            if last_purchase > customer.last_purchase_date:
                customer.last_purchase_date = last_purchase
        else:
            customer = Customer(
                customer_id=customer_id,
                country=country,
                first_purchase_date=first_purchase,
                last_purchase_date=last_purchase,
            )
            self.session.add(customer)
        return customer

    def count(self) -> int:
        return self.session.query(Customer).count()

    def delete_all(self):
        self.session.query(Customer).delete()


class TransactionRepository:
    def __init__(self, session: Optional[Session] = None):
        self.session = session or get_session()

    def get_by_customer(self, customer_id: int) -> list[Transaction]:
        return (
            self.session.query(Transaction)
            .filter_by(customer_id=customer_id)
            .order_by(Transaction.invoice_date.desc())
            .all()
        )

    def bulk_insert(self, transactions: list[dict]):
        self.session.bulk_insert_mappings(Transaction, transactions)

    def count(self) -> int:
        return self.session.query(Transaction).count()

    def delete_all(self):
        self.session.query(Transaction).delete()


class RFMRepository:
    def __init__(self, session: Optional[Session] = None):
        self.session = session or get_session()

    def get_all(self) -> list[RFMScore]:
        return self.session.query(RFMScore).all()

    def get_by_customer(self, customer_id: int) -> Optional[RFMScore]:
        return self.session.query(RFMScore).filter_by(customer_id=customer_id).first()

    def upsert(self, data: dict) -> RFMScore:
        score = self.get_by_customer(data["customer_id"])
        if score:
            for key, value in data.items():
                setattr(score, key, value)
        else:
            score = RFMScore(**data)
            self.session.add(score)
        return score

    def bulk_upsert(self, records: list[dict]):
        for record in records:
            self.upsert(record)

    def delete_all(self):
        self.session.query(RFMScore).delete()


class SegmentRepository:
    def __init__(self, session: Optional[Session] = None):
        self.session = session or get_session()

    def get_all(self) -> list[Segment]:
        return self.session.query(Segment).all()

    def get_by_customer(self, customer_id: int) -> Optional[Segment]:
        return self.session.query(Segment).filter_by(customer_id=customer_id).first()

    def upsert(self, data: dict) -> Segment:
        segment = self.get_by_customer(data["customer_id"])
        if segment:
            for key, value in data.items():
                setattr(segment, key, value)
        else:
            segment = Segment(**data)
            self.session.add(segment)
        return segment

    def delete_all(self):
        self.session.query(Segment).delete()
