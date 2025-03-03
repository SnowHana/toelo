# footy/src/footy/database.py
import psycopg
import pandas as pd
from footy.player_elo.database_connection import (
    DatabaseConnection,
    DATABASE_CONFIG,
    get_engine,
)


def get_player_data(query: str) -> pd.DataFrame:
    """Fetch data from the players table using a given SQL query."""
    engine = get_engine()
    df = pd.read_sql_query(query, engine)
    return df
