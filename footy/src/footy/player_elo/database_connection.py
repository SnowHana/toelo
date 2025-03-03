from pathlib import Path
from typing import Dict

import psycopg

DATA_DIR = Path(__file__).resolve().parents[2] / "data"


DATABASE_CONFIG = {
    "dbname": "football",
    "user": "postgres",
    "password": "1234",
    "host": "localhost",
    "port": "5432",
}


class DatabaseConnection:
    """
    Set up connection with PostgreSQL database
    """

    def __init__(self, config: Dict[str, str]):
        self.config = config
        self.conn = None

    def __enter__(self):
        self.conn = psycopg.connect(**self.config)
        return self.conn

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
            self.conn.close()
