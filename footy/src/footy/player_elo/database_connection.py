from pathlib import Path
from typing import Dict

import psycopg
from sqlalchemy import create_engine

DATA_DIR = Path(__file__).resolve().parents[2] / "data"


DATABASE_CONFIG = {
    "dbname": "football",
    "user": "postgres",
    "password": "1234",
    "host": "localhost",
    "port": "5432",
}


def get_connection_string(config: Dict[str, str]) -> str:
    """Return a SQLAlchemy-compatible connection string."""
    return (
        f"postgresql+psycopg2://{config['user']}:{config['password']}"
        f"@{config['host']}:{config['port']}/{config['dbname']}"
    )


def get_engine(config: Dict[str, str] = DATABASE_CONFIG):
    """Create and return an SQLAlchemy engine based on the given configuration."""
    conn_str = get_connection_string(config)
    engine = create_engine(conn_str)
    return engine


# class DatabaseConnection:
#     """
#     Set up connection with PostgreSQL database
#     """

#     def __init__(self, config: Dict[str, str]):
#         self.config = config
#         self.conn = None

#     def __enter__(self):
#         self.conn = psycopg.connect(**self.config)
#         return self.conn

#     def __exit__(self, exc_type, exc_val, exc_tb):
#         if self.conn:
#             self.conn.close()
