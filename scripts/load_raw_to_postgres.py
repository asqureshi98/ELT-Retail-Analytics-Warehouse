from __future__ import annotations

import argparse
import os
from pathlib import Path

import pandas as pd
import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import execute_values

TABLE_ORDER = [
    "customers",
    "products",
    "stores",
    "promotions",
    "orders",
    "order_items",
    "payments",
    "inventory",
    "returns",
]


def get_connection():
    load_dotenv()
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        dbname=os.getenv("POSTGRES_DB", "retail_warehouse"),
        user=os.getenv("POSTGRES_USER", "retail_user"),
        password=os.getenv("POSTGRES_PASSWORD", "retail_password"),
    )


def _insert_dataframe(cursor, table_name: str, df: pd.DataFrame) -> None:
    if df.empty:
        return
    columns = list(df.columns)
    records = [tuple(None if pd.isna(value) else value for value in row) for row in df.to_numpy()]
    column_sql = ", ".join(columns)
    sql = f"INSERT INTO raw.{table_name} ({column_sql}) VALUES %s"
    execute_values(cursor, sql, records, page_size=1000)


def load_raw_to_postgres(input_dir: str | Path) -> None:
    input_path = Path(input_dir)
    conn = get_connection()
    batch_run_id = None
    try:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO audit.batch_runs (status) VALUES ('running') RETURNING batch_run_id"
                )
                batch_run_id = cursor.fetchone()[0]

                for table in reversed(TABLE_ORDER):
                    cursor.execute(f"TRUNCATE TABLE raw.{table} RESTART IDENTITY CASCADE")

                for table in TABLE_ORDER:
                    filename = f"{table}.csv"
                    path = input_path / filename
                    try:
                        df = pd.read_csv(path)
                        df = df.where(pd.notnull(df), None)
                        _insert_dataframe(cursor, table, df)
                        cursor.execute(
                            """
                            INSERT INTO audit.file_loads
                                (batch_run_id, file_name, target_table, row_count, status)
                            VALUES (%s, %s, %s, %s, 'success')
                            """,
                            (batch_run_id, filename, f"raw.{table}", len(df)),
                        )
                        print(f"Loaded {filename}: {len(df)} rows")
                    except Exception as exc:
                        cursor.execute(
                            """
                            INSERT INTO audit.file_loads
                                (batch_run_id, file_name, target_table, row_count, status, error_message)
                            VALUES (%s, %s, %s, 0, 'failed', %s)
                            """,
                            (batch_run_id, filename, f"raw.{table}", str(exc)),
                        )
                        raise

                cursor.execute(
                    """
                    UPDATE audit.batch_runs
                    SET status = 'success', finished_at = CURRENT_TIMESTAMP
                    WHERE batch_run_id = %s
                    """,
                    (batch_run_id,),
                )
        print("Batch load succeeded")
    except Exception as exc:
        conn.rollback()
        if batch_run_id is not None:
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        """
                        UPDATE audit.batch_runs
                        SET status = 'failed', finished_at = CURRENT_TIMESTAMP, error_message = %s
                        WHERE batch_run_id = %s
                        """,
                        (str(exc), batch_run_id),
                    )
        raise
    finally:
        conn.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Load raw retail CSV files into PostgreSQL.")
    parser.add_argument("--input-dir", default="data/raw")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    load_raw_to_postgres(args.input_dir)


if __name__ == "__main__":
    main()
