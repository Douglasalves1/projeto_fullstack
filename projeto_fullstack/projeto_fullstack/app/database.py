"""
Módulo de banco de dados - SQLite com context manager
"""

import sqlite3
from contextlib import contextmanager

DB_PATH = "data/vendas.db"

def init_db():
    """Cria as tabelas se não existirem."""
    import os
    os.makedirs("data", exist_ok=True)
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS vendas (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                produto     TEXT    NOT NULL,
                categoria   TEXT    NOT NULL,
                quantidade  INTEGER NOT NULL,
                preco_unitario REAL NOT NULL,
                total       REAL    NOT NULL,
                regiao      TEXT    NOT NULL,
                data        TEXT    NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS etl_runs (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                executado_em TEXT NOT NULL,
                registros   INTEGER,
                status      TEXT,
                detalhes    TEXT
            )
        """)

@contextmanager
def get_connection():
    """Context manager para conexão SQLite com row_factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
