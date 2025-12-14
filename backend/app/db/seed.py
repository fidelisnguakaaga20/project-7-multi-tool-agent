# /// Stage 5: create + seed a local SQLite database (read-only usage by agent)
from __future__ import annotations

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "sample.sqlite"


def seed(db_path: Path = DB_PATH) -> str:
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()

    # /// reset
    cur.execute("DROP TABLE IF EXISTS customers;")
    cur.execute("DROP TABLE IF EXISTS orders;")
    cur.execute("DROP TABLE IF EXISTS tickets;")

    # /// schema
    cur.execute("""
    CREATE TABLE customers (
      id INTEGER PRIMARY KEY,
      name TEXT NOT NULL,
      email TEXT NOT NULL UNIQUE,
      country TEXT NOT NULL
    );
    """)

    cur.execute("""
    CREATE TABLE orders (
      id INTEGER PRIMARY KEY,
      customer_id INTEGER NOT NULL,
      amount REAL NOT NULL,
      status TEXT NOT NULL,
      created_at TEXT NOT NULL,
      FOREIGN KEY(customer_id) REFERENCES customers(id)
    );
    """)

    cur.execute("""
    CREATE TABLE tickets (
      id INTEGER PRIMARY KEY,
      customer_id INTEGER NOT NULL,
      subject TEXT NOT NULL,
      priority TEXT NOT NULL,
      status TEXT NOT NULL,
      created_at TEXT NOT NULL,
      FOREIGN KEY(customer_id) REFERENCES customers(id)
    );
    """)

    # /// seed data
    customers = [
        (1, "Ada Okoye", "ada@example.com", "NG"),
        (2, "John Smith", "john@example.com", "US"),
        (3, "Fatima Bello", "fatima@example.com", "NG"),
        (4, "Marie Dubois", "marie@example.com", "FR"),
        (5, "Ken Tanaka", "ken@example.com", "JP"),
    ]
    cur.executemany("INSERT INTO customers (id, name, email, country) VALUES (?, ?, ?, ?);", customers)

    orders = [
        (1, 1, 120.50, "paid", "2025-12-01"),
        (2, 1, 80.00, "paid", "2025-12-03"),
        (3, 2, 250.00, "paid", "2025-12-02"),
        (4, 3, 35.00, "refunded", "2025-12-04"),
        (5, 4, 400.00, "paid", "2025-12-05"),
        (6, 5, 15.99, "pending", "2025-12-06"),
        (7, 2, 99.99, "paid", "2025-12-07"),
        (8, 3, 210.00, "paid", "2025-12-08"),
    ]
    cur.executemany(
        "INSERT INTO orders (id, customer_id, amount, status, created_at) VALUES (?, ?, ?, ?, ?);",
        orders
    )

    tickets = [
        (1, 1, "Login issue", "high", "open", "2025-12-02"),
        (2, 2, "Billing question", "medium", "closed", "2025-12-03"),
        (3, 3, "Refund status", "high", "open", "2025-12-05"),
        (4, 4, "Change email", "low", "closed", "2025-12-06"),
        (5, 5, "Order delay", "medium", "open", "2025-12-07"),
    ]
    cur.executemany(
        "INSERT INTO tickets (id, customer_id, subject, priority, status, created_at) VALUES (?, ?, ?, ?, ?, ?);",
        tickets
    )

    conn.commit()
    conn.close()
    return str(db_path)


if __name__ == "__main__":
    print("Seeded DB at:", seed())
