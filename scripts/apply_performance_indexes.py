#!/usr/bin/env python3
"""Apply Sprint 6 performance indexes using psycopg2.

This avoids requiring a host `psql` binary while still keeping the index SQL in a
plain, reviewable file.
"""

from __future__ import annotations

import os
from pathlib import Path

import psycopg2

DEFAULT_SQL_PATH = Path("warehouse/hardening/004_create_performance_indexes.sql")


def build_connection_kwargs() -> dict[str, str | int]:
    return {
        "host": os.getenv("POSTGRES_HOST", "localhost"),
        "port": int(os.getenv("POSTGRES_PORT", "5432")),
        "dbname": os.getenv("POSTGRES_DB", "retail_warehouse"),
        "user": os.getenv("POSTGRES_USER", "retail_user"),
        "password": os.getenv("POSTGRES_PASSWORD", "retail_password"),
    }


def apply_indexes(sql_path: Path = DEFAULT_SQL_PATH) -> None:
    sql = sql_path.read_text(encoding="utf-8")
    kwargs = build_connection_kwargs()
    with psycopg2.connect(
        host=str(kwargs["host"]),
        port=int(kwargs["port"]),
        dbname=str(kwargs["dbname"]),
        user=str(kwargs["user"]),
        password=str(kwargs["password"]),
    ) as connection:
        with connection.cursor() as cursor:
            cursor.execute(sql)


def main() -> int:
    apply_indexes()
    print(f"Applied performance indexes from {DEFAULT_SQL_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
