import os
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, Column, Integer, String, Float, Date, Boolean, PrimaryKeyConstraint
from sqlalchemy.orm import declarative_base, sessionmaker

# Data dir
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR.parents[0] / 'data' / 'transfer_data'

# Replace with your actual database credentials
DATABASE_URI = 'postgresql+psycopg://postgres:1234@localhost:5432/football'
engine = create_engine(DATABASE_URI)

Base = declarative_base()


def _import_dataframes() -> dict:
    """Read data from CSV files and store as DataFrames."""
    global DATA_DIR
    dataframes = {}
    for dirpath, _, filenames in os.walk(DATA_DIR):
        for filename in filenames:
            file_key = f"{filename.split('.')[0]}"
            filepath = os.path.join(dirpath, filename)
            dataframes[file_key] = pd.read_csv(filepath, sep=",", encoding="UTF-8")
            print(f"{file_key}: {dataframes[file_key].shape}")
    print("Data imported successfully.")
    return dataframes


# Define SQLAlchemy models for each DataFrame
class GameLineup(Base):
    __tablename__ = 'game_lineups'

    game_lineups_id = Column(String, primary_key=True)
    date = Column(Date)
    game_id = Column(Integer)
    player_id = Column(Integer)
    club_id = Column(Integer)
    player_name = Column(String)
    type = Column(String)
    position = Column(String)
    number = Column(String)
    team_captain = Column(Integer)


class Competition(Base):
    __tablename__ = 'competitions'

    competition_id = Column(String, primary_key=True)
    competition_code = Column(String)
    name = Column(String)
    sub_type = Column(String)
    type = Column(String)
    country_id = Column(Integer)
    country_name = Column(String)
    domestic_league_code = Column(String)
    confederation = Column(String)
    url = Column(String)
    is_major_national_league = Column(Boolean)


class Appearance(Base):
    __tablename__ = 'appearances'

    appearance_id = Column(String, primary_key=True)
    game_id = Column(Integer)
    player_id = Column(Integer)
    player_club_id = Column(Integer)
    player_current_club_id = Column(Integer)
    date = Column(Date)
    player_name = Column(String)
    competition_id = Column(String)
    yellow_cards = Column(Integer)
    red_cards = Column(Integer)
    goals = Column(Integer)
    assists = Column(Integer)
    minutes_played = Column(Integer)


class PlayerValuation(Base):
    __tablename__ = 'player_valuations'

    player_id = Column(Integer)
    date = Column(Date)
    market_value_in_eur = Column(Integer)
    current_club_id = Column(Integer)
    player_club_domestic_competition_id = Column(String)

    __table_args__ = (
        PrimaryKeyConstraint('player_id', 'date', name='player_valuation_pk'),
    )


class GameEvent(Base):
    __tablename__ = 'game_events'

    game_event_id = Column(String, primary_key=True)
    date = Column(Date)
    game_id = Column(Integer)
    minute = Column(Integer)
    type = Column(String)
    club_id = Column(Integer)
    player_id = Column(Integer)
    description = Column(String)
    player_in_id = Column(Integer)
    player_assist_id = Column(Integer)


class Transfer(Base):
    __tablename__ = 'transfers'

    player_id = Column(Integer)
    transfer_date = Column(Date)
    transfer_season = Column(String)
    from_club_id = Column(Integer)
    to_club_id = Column(Integer)
    from_club_name = Column(String)
    to_club_name = Column(String)
    transfer_fee = Column(Float)
    market_value_in_eur = Column(Float)
    player_name = Column(String)

    __table_args__ = (
        PrimaryKeyConstraint('player_id', 'from_club_id', 'to_club_id', name='transfer_pk'),
    )


class Player(Base):
    __tablename__ = 'players'

    player_id = Column(Integer, primary_key=True)
    first_name = Column(String)
    last_name = Column(String)
    name = Column(String)
    last_season = Column(Integer)
    current_club_id = Column(Integer)
    player_code = Column(String)
    country_of_birth = Column(String)
    city_of_birth = Column(String)
    country_of_citizenship = Column(String)
    date_of_birth = Column(Date)
    sub_position = Column(String)
    position = Column(String)
    foot = Column(String)
    height_in_cm = Column(Float)
    contract_expiration_date = Column(Date)
    agent_name = Column(String)
    image_url = Column(String)
    url = Column(String)
    current_club_domestic_competition_id = Column(String)
    current_club_name = Column(String)
    market_value_in_eur = Column(Float)
    highest_market_value_in_eur = Column(Float)


class Game(Base):
    __tablename__ = 'games'

    game_id = Column(Integer, primary_key=True)
    competition_id = Column(String)
    season = Column(Integer)
    round = Column(String)
    date = Column(Date)
    home_club_id = Column(Integer)
    away_club_id = Column(Integer)
    home_club_goals = Column(Integer)
    away_club_goals = Column(Integer)
    home_club_position = Column(Integer)
    away_club_position = Column(Integer)
    home_club_manager_name = Column(String)
    away_club_manager_name = Column(String)
    stadium = Column(String)
    attendance = Column(Integer)
    referee = Column(String)
    url = Column(String)
    home_club_formation = Column(String)
    away_club_formation = Column(String)
    home_club_name = Column(String)
    away_club_name = Column(String)
    aggregate = Column(String)
    competition_type = Column(String)


class ClubGame(Base):
    __tablename__ = 'club_games'

    game_id = Column(Integer, primary_key=True)
    club_id = Column(Integer)
    own_goals = Column(Integer)
    own_position = Column(Integer)
    own_manager_name = Column(String)
    opponent_id = Column(Integer)
    opponent_goals = Column(Integer)
    opponent_position = Column(Integer)
    opponent_manager_name = Column(String)
    hosting = Column(String)
    is_win = Column(Integer)


class PlayerElo(Base):
    __tablename__ = 'players_elo'

    player_id = Column(Integer)
    season = Column(Integer)
    first_name = Column(String)
    last_name = Column(String)
    name = Column(String)
    player_code = Column(String)
    country_of_birth = Column(String)
    date_of_birth = Column(Date)
    elo = Column(Float)

    __table_args__ = (
        PrimaryKeyConstraint('player_id', 'season', name='player_elo_pk'),
    )


class Club(Base):
    __tablename__ = 'clubs'

    club_id = Column(Integer, primary_key=True)
    club_code = Column(String)
    name = Column(String)
    domestic_competition_id = Column(String)
    total_market_value = Column(Float)
    squad_size = Column(Integer)
    average_age = Column(Float)
    foreigners_number = Column(Integer)
    foreigners_percentage = Column(Float)
    national_team_players = Column(Integer)
    stadium_name = Column(String)
    stadium_seats = Column(Integer)
    net_transfer_record = Column(String)
    coach_name = Column(Float)
    last_season = Column(Integer)
    filename = Column(String)
    url = Column(String)


# Connect to the database (replace with your database URL)
# engine = create_engine('postgresql://username:password@localhost:5432/football')

def create_backup_table(table_name: str, engine):
    """
    Create a backup of a table by copying its structure and data.

    Args:
        table_name (str): Name of the table to back up.
        engine: SQLAlchemy engine object.
    """
    backup_table_name = f"{table_name}_backup"
    with engine.connect() as conn:
        conn.execute(f"DROP TABLE IF EXISTS {backup_table_name};")
        conn.execute(f"""
            CREATE TABLE {backup_table_name} AS
            SELECT * FROM {table_name};
        """)
        print(f"Backup created for table: {table_name} as {backup_table_name}")


def create_process_table(engine):
    with engine.connect() as conn:
        conn.execute(f"""CREATE TABLE IF NOT EXISTS process_progress (
                        process_name VARCHAR PRIMARY KEY,
                        last_processed_date DATE,
                        last_processed_game_id INTEGER);""")

        conn.execute(f"""INSERT INTO process_progress (process_name, last_processed_date, last_processed_game_id)
                        VALUES ('elo_update', NULL, NULL)
                        ON CONFLICT (process_name) DO NOTHING;""")
        print(f"Table created")


def main():
    # Create all tables
    Base.metadata.create_all(engine)

    try:
        create_backup_table('players_elo', engine)
    except Exception as e:
        print(f"Error creating a backup {e}")

    # Load data from CSV files and write to SQL
    dataframes = _import_dataframes()

    # Create a session
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        for table_name, dataframe in dataframes.items():
            dataframe.to_sql(table_name, con=engine, if_exists='replace', index=False)
            print(f"{table_name} is imported.")
        session.commit()
    except Exception as e:
        session.rollback()
        print(f"Error during data import: {e}")
    finally:
        session.close()


if __name__ == "__main__":
    main()

# Create the table in the database
# Base.metadata.create_all(engine)


# players_elo_df = pd.read_csv(os.path.join(DATA_DIR, 'players_elo.csv'))
# players_elo_df.to_sql('players_elo', engine, if_exists='replace', index=False)

# Verify data load
#
# with engine.connect() as conn:
#     result = conn.execute("SELECT * FROM players_elo LIMIT 5")
#     for row in result:
#         print(row)


# import os
# from pathlib import Path
#
# import pandas as pd
# from sqlalchemy import create_engine, Column, Integer, String, Float, Date, Boolean, PrimaryKeyConstraint
# from sqlalchemy.orm import declarative_base, sessionmaker
#
# # Data dir
# BASE_DIR = Path(__file__).resolve().parent
# DATA_DIR = BASE_DIR.parents[0] / 'data' / 'transfer_data'
#
# # Replace with your actual database credentials
# DATABASE_URI = 'postgresql+psycopg://postgres:1234@localhost:5432/football'
# engine = create_engine(DATABASE_URI)
#
# Base = declarative_base()
#
#
# def _import_dataframes() -> dict:
#     """Read data from CSV files and store as DataFrames."""
#     global DATA_DIR
#     dataframes = {}
#     for dirpath, _, filenames in os.walk(DATA_DIR):
#         for filename in filenames:
#             file_key = f"{filename.split('.')[0]}"
#             filepath = os.path.join(dirpath, filename)
#             dataframes[file_key] = pd.read_csv(filepath, sep=",", encoding="UTF-8")
#             # Convert season column to integer if they exist
#             # if 'season' in dataframes[file_key].columns:
#             #     dataframes[file_key]['season'] = dataframes[file_key]['season'].astype(int)
#             print(f"{file_key}: {dataframes[file_key].shape}")
#     print("Data imported successfully.")
#     return dataframes
#
#
# # Define SQLAlchemy models for each DataFrame
# class GameLineup(Base):
#     __tablename__ = 'game_lineups'
#
#     game_lineups_id = Column(String, primary_key=True)
#     date = Column(Date)
#     game_id = Column(Integer)
#     player_id = Column(Integer)
#     club_id = Column(Integer)
#     player_name = Column(String)
#     type = Column(String)
#     position = Column(String)
#     number = Column(String)
#     team_captain = Column(Integer)
#
#
# class Competition(Base):
#     __tablename__ = 'competitions'
#
#     competition_id = Column(String, primary_key=True)
#     competition_code = Column(String)
#     name = Column(String)
#     sub_type = Column(String)
#     type = Column(String)
#     country_id = Column(Integer)
#     country_name = Column(String)
#     domestic_league_code = Column(String)
#     confederation = Column(String)
#     url = Column(String)
#     is_major_national_league = Column(Boolean)
#
#
# class Appearance(Base):
#     __tablename__ = 'appearances'
#
#     appearance_id = Column(String, primary_key=True)
#     game_id = Column(Integer)
#     player_id = Column(Integer)
#     player_club_id = Column(Integer)
#     player_current_club_id = Column(Integer)
#     date = Column(Date)
#     player_name = Column(String)
#     competition_id = Column(String)
#     yellow_cards = Column(Integer)
#     red_cards = Column(Integer)
#     goals = Column(Integer)
#     assists = Column(Integer)
#     minutes_played = Column(Integer)
#
#
# class PlayerValuation(Base):
#     __tablename__ = 'player_valuations'
#
#     player_id = Column(Integer)
#     date = Column(Date)
#     market_value_in_eur = Column(Integer)
#     current_club_id = Column(Integer)
#     player_club_domestic_competition_id = Column(String)
#
#     __table_args__ = (
#         PrimaryKeyConstraint('player_id', 'date', name='player_valuation_pk'),
#     )
#
#
# class GameEvent(Base):
#     __tablename__ = 'game_events'
#
#     game_event_id = Column(String, primary_key=True)
#     date = Column(Date)
#     game_id = Column(Integer)
#     minute = Column(Integer)
#     type = Column(String)
#     club_id = Column(Integer)
#     player_id = Column(Integer)
#     description = Column(String)
#     player_in_id = Column(Integer)
#     player_assist_id = Column(Integer)
#
#
# class Transfer(Base):
#     __tablename__ = 'transfers'
#
#     player_id = Column(Integer)
#     transfer_date = Column(Date)
#     transfer_season = Column(String)
#     from_club_id = Column(Integer)
#     to_club_id = Column(Integer)
#     from_club_name = Column(String)
#     to_club_name = Column(String)
#     transfer_fee = Column(Float)
#     market_value_in_eur = Column(Float)
#     player_name = Column(String)
#
#     __table_args__ = (
#         PrimaryKeyConstraint('player_id', 'from_club_id', 'to_club_id', name='transfer_pk'),
#     )
#
#
# class Player(Base):
#     __tablename__ = 'players'
#
#     player_id = Column(Integer, primary_key=True)
#     first_name = Column(String)
#     last_name = Column(String)
#     name = Column(String)
#     last_season = Column(Integer)
#     current_club_id = Column(Integer)
#     player_code = Column(String)
#     country_of_birth = Column(String)
#     city_of_birth = Column(String)
#     country_of_citizenship = Column(String)
#     date_of_birth = Column(Date)
#     sub_position = Column(String)
#     position = Column(String)
#     foot = Column(String)
#     height_in_cm = Column(Float)
#     contract_expiration_date = Column(Date)
#     agent_name = Column(String)
#     image_url = Column(String)
#     url = Column(String)
#     current_club_domestic_competition_id = Column(String)
#     current_club_name = Column(String)
#     market_value_in_eur = Column(Float)
#     highest_market_value_in_eur = Column(Float)
#
#
# class Game(Base):
#     __tablename__ = 'games'
#
#     game_id = Column(Integer, primary_key=True)
#     competition_id = Column(String)
#     season = Column(Integer)
#     round = Column(String)
#     date = Column(Date)
#     home_club_id = Column(Integer)
#     away_club_id = Column(Integer)
#     home_club_goals = Column(Integer)
#     away_club_goals = Column(Integer)
#     home_club_position = Column(Integer)
#     away_club_position = Column(Integer)
#     home_club_manager_name = Column(String)
#     away_club_manager_name = Column(String)
#     stadium = Column(String)
#     attendance = Column(Integer)
#     referee = Column(String)
#     url = Column(String)
#     home_club_formation = Column(String)
#     away_club_formation = Column(String)
#     home_club_name = Column(String)
#     away_club_name = Column(String)
#     aggregate = Column(String)
#     competition_type = Column(String)
#
#
# class ClubGame(Base):
#     __tablename__ = 'club_games'
#
#     game_id = Column(Integer, primary_key=True)
#     club_id = Column(Integer)
#     own_goals = Column(Integer)
#     own_position = Column(Integer)
#     own_manager_name = Column(String)
#     opponent_id = Column(Integer)
#     opponent_goals = Column(Integer)
#     opponent_position = Column(Integer)
#     opponent_manager_name = Column(String)
#     hosting = Column(String)
#     is_win = Column(Integer)
#
#
# class PlayerElo(Base):
#     __tablename__ = 'players_elo'
#
#     player_id = Column(Integer)
#     season = Column(Integer)
#     first_name = Column(String)
#     last_name = Column(String)
#     name = Column(String)
#     player_code = Column(String)
#     country_of_birth = Column(String)
#     date_of_birth = Column(Date)
#     elo = Column(Float)
#
#     __table_args__ = (
#         PrimaryKeyConstraint('player_id', 'season', name='player_elo_pk'),
#     )
#
#
# class Club(Base):
#     __tablename__ = 'clubs'
#
#     club_id = Column(Integer, primary_key=True)
#     club_code = Column(String)
#     name = Column(String)
#     domestic_competition_id = Column(String)
#     total_market_value = Column(Float)
#     squad_size = Column(Integer)
#     average_age = Column(Float)
#     foreigners_number = Column(Integer)
#     foreigners_percentage = Column(Float)
#     national_team_players = Column(Integer)
#     stadium_name = Column(String)
#     stadium_seats = Column(Integer)
#     net_transfer_record = Column(String)
#     coach_name = Column(Float)
#     last_season = Column(Integer)
#     filename = Column(String)
#     url = Column(String)
#
#
# # Connect to the database (replace with your database URL)
# # engine = create_engine('postgresql://username:password@localhost:5432/football')
#
#
# def main():
#     # Create all tables
#     Base.metadata.create_all(engine)
#
#     # Load data from CSV files and write to SQL
#     dataframes = _import_dataframes()
#
#     # Create a session
#     Session = sessionmaker(bind=engine)
#     session = Session()
#
#     for table_name, dataframe in dataframes.items():
#         dataframe.to_sql(table_name, con=engine, if_exists='replace', index=False)
#         print(f"{table_name} is imported.")
#
#     # Commit the session and close
#     session.commit()
#     session.close()
#
#
# if __name__ == "__main__":
#     main()
# # Create the table in the database
# # Base.metadata.create_all(engine)
#
#
# # players_elo_df = pd.read_csv(os.path.join(DATA_DIR, 'players_elo.csv'))
# # players_elo_df.to_sql('players_elo', engine, if_exists='replace', index=False)
#
# # Verify data load
# #
# # with engine.connect() as conn:
# #     result = conn.execute("SELECT * FROM players_elo LIMIT 5")
# #     for row in result:
# #         print(row)
