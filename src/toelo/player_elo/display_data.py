# footy/src/footy/database.py
import psycopg
import pandas as pd
from sqlalchemy import text
from toelo.player_elo.database_connection import (
    DATABASE_CONFIG,
    get_engine,
)
import plotly.express as px


def get_player_data(query: str) -> pd.DataFrame:
    """Fetch data from the players table using a given SQL query."""
    engine = get_engine()
    df = pd.read_sql_query(query, engine)
    return df


def get_player_names(player_name_q: str):
    pattern = f"%{player_name_q}%"
    engine = get_engine()

    with engine.connect() as conn:
        res = conn.execute(
            text("SELECT name FROM players WHERE name ILIKE :x"),
            {"x": pattern},
        ).fetchall()

    return [row[0] for row in res]


def get_indiv_player_elo_data(player_name: str) -> pd.DataFrame:
    engine = get_engine()
    with engine.connect() as conn:
        res = conn.execute(
            text("""SELECT * FROM players_elo WHERE name LIKE :x"""), {"x": player_name}
        ).fetchall()

    df = pd.DataFrame(res)
    # df.columns = res.keys()
    df.dropna(subset=["elo"], inplace=True)
    sort_by_elo = df.sort_values("elo", ascending=True)
    sort_by_elo["season"].astype("Int64")
    sort_by_elo["name_season"] = (
        sort_by_elo["name"] + " - " + sort_by_elo["season"].astype(str)
    )
    return sort_by_elo


def plot_top_elo_players():
    """Plot top elo players as a bar graph

    Returns:
        Figure: plotly.express.bar type bar graph
    """
    query = (
        "SELECT * FROM players_elo WHERE elo IS NOT NULL ORDER BY elo DESC LIMIT 200;"
    )
    df = get_player_data(query)
    df = df.head(20)
    sort_by_elo = df.sort_values("elo", ascending=True)[::-1]

    sort_by_elo["name_season"] = (
        sort_by_elo["name"] + " - " + sort_by_elo["season"].astype(str)
    )

    fig = px.bar(
        sort_by_elo,
        y="name_season",
        x="elo",
        color="elo",
        color_continuous_scale="reds",
    )
    # fig = px.bar(sort_by_elo, y='name', x='elo')

    fig.update_layout(
        height=700, title="Seasonal ELOs of players top 20", plot_bgcolor="rgb(56,0,60)"
    )

    fig.update_yaxes(title_text="Players", showgrid=False)
    fig.update_xaxes(title_text="Seasonal ELOs", showgrid=False)
    return fig
