from footy.player_elo.database_connection import (
    DATABASE_CONFIG,
    get_engine,
)


# Constants
# BASE_ELO = 1500
# ELO_RANGE = 300


class PlayersEloReinitialiser:
    """Initialize Player ELO based on SQL operations.
    @precondition: players_elo.csv file is alr created, player ELO value might not be accurate.
    @precondition: PostGre SQL database is alr created."""

    def __init__(self, cur, base_elo, elo_range):
        """
        @param cur: DB cursor
        @param base_elo:
        @param elo_range:
        """
        self.cur = cur
        self.base_elo = base_elo
        self.elo_range = elo_range

    def reset_elo_column(self):
        """Reset the ELO column for all players in the players_elo table."""
        print("Resetting ELO column...")
        self.cur.execute(
            """
            UPDATE players_elo
            SET elo = NULL;
        """
        )

        self.cur.connection.commit()
        print("ELO column reset successfully.")

    def init_season_valuations(self):
        """Calculate mean and std of player valuations per season, storing in SQL for fast access."""
        # Calculate mean and std of log-transformed values for each season and store them in a new table
        self.cur.execute(
            """
            DROP TABLE IF EXISTS season_valuations;
            CREATE TABLE season_valuations AS
            SELECT 
                EXTRACT(YEAR FROM p.date::date) AS season,  -- Alias the extracted year as `season`
                AVG(LOG(1 + p.market_value_in_eur)) AS mean_log,
                STDDEV(LOG(1 + p.market_value_in_eur)) AS std_log
            FROM player_valuations p
            GROUP BY season;
        """
        )

        self.cur.connection.commit()
        print("Season valuations initialized.")

    def fill_season_gaps(self):
        """Fill missing seasons for each player directly in SQL."""
        # Using a recursive CTE to generate continuous seasons for each player
        self.cur.execute(
            """
            WITH RECURSIVE seasons AS (
                SELECT DISTINCT player_id, season AS min_season, season AS max_season
                FROM players_elo
                UNION
                SELECT player_id, min_season, min_season + 1
                FROM seasons
                WHERE min_season + 1 <= max_season
            )
            INSERT INTO players_elo (player_id, season)
            SELECT s.player_id, s.min_season
            FROM seasons s
            LEFT JOIN players_elo p ON s.player_id = p.player_id AND s.min_season = p.season
            WHERE p.season IS NULL;
        """
        )

        self.cur.connection.commit()
        print("Season gaps filled for players.")

    def init_player_elo_with_value(self):
        """Initialize ELO based on market value for each player per season using SQL."""
        # Initialize ELO based on z-score calculation
        self.cur.execute(
            f"""
            UPDATE players_elo
            SET elo = {self.base_elo} + (
                (LOG(1 + pv.market_value_in_eur) - sv.mean_log) / NULLIF(sv.std_log, 0)
                * {self.elo_range / 2}
            )
            FROM player_valuations pv
            JOIN season_valuations sv ON EXTRACT(YEAR FROM pv.date::date) = sv.season
            WHERE players_elo.player_id = pv.player_id
            AND players_elo.season = EXTRACT(YEAR FROM pv.date::date)
            AND players_elo.elo IS NULL;
        """
        )

        self.cur.connection.commit()
        print("Player ELO initialized based on market value.")

    def init_all_players_elo(self):
        """Main function to initialize all player ELOs."""
        self.reset_elo_column()
        self.init_season_valuations()
        self.fill_season_gaps()
        self.init_player_elo_with_value()
        print("All player ELOs initialized.")
        self.cur.execute(
            f"""
            SELECT name, elo
            FROM players_elo
            WHERE elo IS NOT NULL
            ORDER BY elo DESC
            LIMIT 1;"""
        )
        print("Maximum ELO: ", self.cur.fetchone())

        self.cur.execute(
            f"""
                    SELECT name, elo
                    FROM players_elo
                    WHERE elo IS NOT NULL
                    ORDER BY elo
                    LIMIT 1;"""
        )
        print("Minimum ELO: ", self.cur.fetchone())

        # Commit the transaction
        self.cur.connection.commit()
        print("Changes committed to the database.")

    def reset_process_progress(self):
        self.cur.execute(
            f"""
                INSERT INTO process_progress (
            process_name,
            last_processed_date,
            last_processed_game_id
        )
        VALUES (
            'elo_update',
            NULL,
            NULL
        )
        ON CONFLICT (process_name)
        DO UPDATE
            SET last_processed_date = EXCLUDED.last_processed_date,
                last_processed_game_id = EXCLUDED.last_processed_game_id;
        """
        )

        self.cur.connection.commit()
        print("Process Progress reset is completed.")


def reset_init_players_elo_db():
    """
    Reset players ELO table and process_progress table in PostgrSQL Database
    """
    # with DatabaseConnection(DATABASE_CONFIG) as conn:
    with get_engine().connect() as conn:
        with conn.cursor() as cur:
            base_elo = int(input("Enter Base ELO: (Default 2500) ").strip() or 2500)
            elo_range = int(input("Enter ELO range: (Default 500) ").strip() or 500)
            elo_reinit = PlayersEloReinitialiser(cur, base_elo, elo_range)
            elo_reinit.init_all_players_elo()
            elo_reinit.reset_process_progress()


# Usage
if __name__ == "__main__":
    reset_init_players_elo_db()

    # elo_reinit.reset_elo_column()
