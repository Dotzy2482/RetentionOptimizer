import pandas as pd
from typing import Optional

from config import DATASET_PATH
from data.database import get_session, init_db
from data.repository import CustomerRepository, TransactionRepository


class ImportResult:
    """Holds cleaning/import statistics."""
    def __init__(self):
        self.total_raw = 0
        self.removed_null_customer = 0
        self.removed_negative_qty = 0
        self.removed_cancelled = 0
        self.removed_bad_date = 0
        self.removed_duplicates = 0
        self.total_clean = 0
        self.customer_count = 0
        self.transaction_count = 0

    @property
    def total_removed(self) -> int:
        return self.total_raw - self.total_clean


class ImportService:
    """Reads Excel/CSV retail data, cleans it, and loads into SQLite."""

    def __init__(self, file_path: Optional[str] = None):
        self.file_path = file_path or DATASET_PATH

    def read_file(self) -> pd.DataFrame:
        """Read Excel (all sheets) or CSV file."""
        import os
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"Dosya bulunamadi: {self.file_path}")

        path = self.file_path.lower()
        try:
            if path.endswith(".csv"):
                df = pd.read_csv(self.file_path)
            else:
                xlsx = pd.ExcelFile(self.file_path)
                frames = [pd.read_excel(xlsx, sheet_name=sheet) for sheet in xlsx.sheet_names]
                df = pd.concat(frames, ignore_index=True)
        except Exception as e:
            raise ValueError(f"Dosya okunamadi. Dosya bozuk veya desteklenmeyen formatta olabilir.\n{e}")

        required_cols = {"Customer ID", "Invoice", "InvoiceDate", "Quantity", "Price"}
        missing = required_cols - set(df.columns.str.strip())
        if missing:
            raise ValueError(f"Dosyada gerekli sutunlar eksik: {', '.join(sorted(missing))}")

        return df

    def clean(self, df: pd.DataFrame) -> tuple[pd.DataFrame, ImportResult]:
        """Clean the raw dataframe and return stats."""
        result = ImportResult()
        result.total_raw = len(df)

        # Standardize column names
        df.columns = df.columns.str.strip()

        # 1. Drop missing Customer ID
        before = len(df)
        df = df.dropna(subset=["Customer ID"])
        result.removed_null_customer = before - len(df)
        df["Customer ID"] = df["Customer ID"].astype(int)

        # 2. Filter non-positive Quantity
        before = len(df)
        df = df[df["Quantity"] > 0]
        result.removed_negative_qty = before - len(df)

        # 3. Filter cancelled invoices (starting with "C")
        before = len(df)
        df["Invoice"] = df["Invoice"].astype(str).str.strip()
        df = df[~df["Invoice"].str.startswith("C")]
        result.removed_cancelled = before - len(df)

        # 4. Parse dates
        before = len(df)
        df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"], errors="coerce")
        df = df.dropna(subset=["InvoiceDate"])
        result.removed_bad_date = before - len(df)

        # 5. Filter non-positive Price
        df = df[df["Price"] > 0]

        # 6. Strip string columns
        for col in ["StockCode", "Description", "Country"]:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()

        # 7. Drop duplicates
        before = len(df)
        df = df.drop_duplicates()
        result.removed_duplicates = before - len(df)

        result.total_clean = len(df)
        result.customer_count = df["Customer ID"].nunique()

        return df.reset_index(drop=True), result

    def load_to_db(self, df: pd.DataFrame, result: ImportResult,
                   progress_callback=None) -> ImportResult:
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
            total_rows = len(df)
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
                    pct = 50 + int((i / total_rows) * 50)
                    progress_callback(pct)

            transaction_repo.bulk_insert(tx_records)
            session.commit()

            if progress_callback:
                progress_callback(100)

            result.transaction_count = len(tx_records)
            result.customer_count = total_customers
            return result

        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def run(self, progress_callback=None) -> ImportResult:
        """Full import pipeline: read -> clean -> load."""
        df = self.read_file()
        df, result = self.clean(df)
        return self.load_to_db(df, result, progress_callback)
