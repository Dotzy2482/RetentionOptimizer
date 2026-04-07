import pandas as pd
import numpy as np
from typing import Optional

from config import DATASET_PATH
from data.database import get_session, init_db
from data.repository import CustomerRepository, TransactionRepository


class ImportService:
    """Reads the Online Retail II Excel file, cleans the data, and loads it into SQLite."""

    def __init__(self, file_path: Optional[str] = None):
        self.file_path = file_path or DATASET_PATH

    def read_excel(self) -> pd.DataFrame:
        """Read all sheets from the Excel file and concatenate them."""
        xlsx = pd.ExcelFile(self.file_path)
        frames = [pd.read_excel(xlsx, sheet_name=sheet) for sheet in xlsx.sheet_names]
        df = pd.concat(frames, ignore_index=True)
        return df

    def clean(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean the raw dataframe:
        - Drop rows with missing Customer ID
        - Remove rows with non-positive Quantity (returns/cancellations)
        - Remove rows with non-positive Price
        - Parse InvoiceDate to datetime
        - Strip whitespace from string columns
        - Drop duplicates
        """
        initial_len = len(df)

        # Standardize column names
        df.columns = df.columns.str.strip()

        # Drop missing Customer ID
        df = df.dropna(subset=["Customer ID"])
        df["Customer ID"] = df["Customer ID"].astype(int)

        # Filter out non-positive quantities and prices
        df = df[df["Quantity"] > 0]
        df = df[df["Price"] > 0]

        # Parse dates
        df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"], errors="coerce")
        df = df.dropna(subset=["InvoiceDate"])

        # Strip string columns
        for col in ["Invoice", "StockCode", "Description", "Country"]:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()

        # Drop exact duplicates
        df = df.drop_duplicates()

        cleaned_len = len(df)
        removed = initial_len - cleaned_len
        print(f"[ImportService] Cleaned: {initial_len} -> {cleaned_len} rows ({removed} removed)")

        return df.reset_index(drop=True)

    def load_to_db(self, df: pd.DataFrame, progress_callback=None):
        """Insert cleaned data into SQLite tables."""
        init_db()
        session = get_session()

        try:
            customer_repo = CustomerRepository(session)
            transaction_repo = TransactionRepository(session)

            # Clear existing data
            transaction_repo.delete_all()
            customer_repo.delete_all()
            session.flush()

            # Build customer aggregates
            customer_agg = (
                df.groupby("Customer ID")
                .agg(
                    country=("Country", "first"),
                    first_purchase=("InvoiceDate", "min"),
                    last_purchase=("InvoiceDate", "max"),
                )
                .reset_index()
            )

            total_customers = len(customer_agg)
            for i, row in customer_agg.iterrows():
                customer_repo.upsert(
                    customer_id=int(row["Customer ID"]),
                    country=row["country"],
                    first_purchase=row["first_purchase"].to_pydatetime(),
                    last_purchase=row["last_purchase"].to_pydatetime(),
                )
                if progress_callback and i % 500 == 0:
                    progress_callback(int((i / total_customers) * 50))

            session.flush()

            # Bulk insert transactions
            tx_records = []
            for i, row in df.iterrows():
                tx_records.append({
                    "invoice_no": str(row["Invoice"]),
                    "customer_id": int(row["Customer ID"]),
                    "stock_code": str(row["StockCode"]),
                    "description": str(row.get("Description", "")),
                    "quantity": int(row["Quantity"]),
                    "price": float(row["Price"]),
                    "invoice_date": row["InvoiceDate"].to_pydatetime(),
                })

                if progress_callback and i % 5000 == 0:
                    pct = 50 + int((i / len(df)) * 50)
                    progress_callback(pct)

            transaction_repo.bulk_insert(tx_records)
            session.commit()

            if progress_callback:
                progress_callback(100)

            print(f"[ImportService] Loaded {total_customers} customers, {len(tx_records)} transactions")
            return total_customers, len(tx_records)

        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def run(self, progress_callback=None) -> tuple[int, int]:
        """Full import pipeline: read -> clean -> load."""
        df = self.read_excel()
        df = self.clean(df)
        return self.load_to_db(df, progress_callback)
