import logging
import sys
from functools import partial
from logging.handlers import RotatingFileHandler
from multiprocessing import Pool
from pathlib import Path

from footy.player_elo.club_analysis import ClubAnalysis
from footy.player_elo.database_connection import DatabaseConnection, DATABASE_CONFIG
from footy.player_elo.game_analysis import GameAnalysis
from footy.player_elo.player_analysis import PlayerAnalysis

# Add the src directory to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))


class EloUpdater:
    """Class for updating ELOs based on game data."""

    BATCH_SIZE = 100  # Number of games processed per batch
    PLAYER_BATCH_LIMIT = 1000  # Maximum player ELO updates before flushing

    def __init__(self, cur, max_games_to_process=1000):
        self.cur = cur
        self.current_game_id = None  # Track the current game ID being processed
        self.games_processed = 0  # Counter for the total games processed
        self.MAX_GAMES_TO_PROCESS = max_games_to_process

    def _get_last_processed_game(self) -> tuple:
        """
        Fetch the last processed game date and game ID from the progress tracker.
        Return (None, None) if there is no last processed game (ie. Initialising)
        @return: (last_processed_date: Date, last_processed_game_id: int)
        @rtype: tuple (Date, Int)
        """
        self.cur.execute(
            """
            SELECT last_processed_date, last_processed_game_id
            FROM process_progress
            WHERE process_name = 'elo_update';
        """
        )
        result = self.cur.fetchone()

        return result if result else (None, None)

    def _update_progress(self, last_game_date: str, last_game_id: int) -> None:
        """
        Update and commit the progress tracker with the last processed game date and game ID
        @param last_game_date: Date of the last processed game
        @param last_game_id: ID of last processed game ID

        @return: None
        """
        self.cur.execute(
            """
            UPDATE process_progress
            SET last_processed_date = %s, last_processed_game_id = %s
            WHERE process_name = 'elo_update';
        """,
            (last_game_date, last_game_id),
        )
        self.cur.connection.commit()

    def fetch_games_to_process(self):
        """
        Fetch the list of games to process.
        @return: List of games to process (game_id, date) of valid games
        """
        last_processed_date, last_processed_game_id = self._get_last_processed_game()

        if last_processed_date:
            # Count and log remaining games to process
            self.cur.execute(
                """
                                SELECT COUNT(*) FROM valid_games
                                WHERE (date::DATE >  %s::DATE OR (date::DATE = %s::DATE AND game_id > %s));""",
                (last_processed_date, last_processed_date, last_processed_game_id),
            )
            logging.info(f"Remaining games to analyse: {self.cur.fetchone()[0]}")

            # Bulk-fetch batch sized games data
            self.cur.execute(
                """
                    SELECT game_id, date 
                    FROM valid_games 
                    WHERE (date::DATE > %s::DATE OR (date::DATE = %s::DATE AND game_id > %s))
                    ORDER BY date, game_id ASC
                    LIMIT %s;
                """,
                (
                    last_processed_date,
                    last_processed_date,
                    last_processed_game_id,
                    self.MAX_GAMES_TO_PROCESS,
                ),
            )
        else:
            self.cur.execute("""SELECT COUNT(*) FROM valid_games;""")
            logging.info(f"Remaining games to analyse: {self.cur.fetchone()[0]}")

            # Start from scratch
            self.cur.execute(
                """
                    SELECT game_id, date 
                    FROM valid_games 
                    ORDER BY date, game_id ASC
                    LIMIT %s;
                """,
                (self.MAX_GAMES_TO_PROCESS,),
            )

        return self.cur.fetchall()

    @staticmethod
    def process_game(game, db_config):
        """
        Static method to process a SINGLE game and return player ELO updates.

        @param game: (game_id, game_date)
        @param db_config: Database Config
        @return: Tuple (game_id, game_date, player_elo_updates) or None if there's an error
        """
        game_id, game_date = game
        player_elo_updates = []
        try:
            # Each process opens its own database connection
            with DatabaseConnection(db_config) as conn:
                with conn.cursor() as cur:
                    logging.info(f"Processing game {game_id} on date {game_date}")

                    game_analysis = GameAnalysis(cur, game_id=game_id)

                    # Club analysis
                    home_club_analysis = ClubAnalysis(
                        game_analysis, game_analysis.home_club_id
                    )
                    away_club_analysis = ClubAnalysis(
                        game_analysis, game_analysis.away_club_id
                    )

                    # Calculate new ELOs
                    new_home_club_elo = home_club_analysis.new_elo()
                    new_away_club_elo = away_club_analysis.new_elo()

                    # Update players' ELO
                    for player_id in game_analysis.players_list:
                        # Case where player_id is null
                        # Log and skip.
                        if player_id is None:
                            logging.error(
                                f"Game {game_id} contains a player with NULL player id."
                            )
                        player_analysis = PlayerAnalysis(game_analysis, player_id)
                        team_change = (
                            new_home_club_elo
                            if player_analysis.club_id == game_analysis.home_club_id
                            else new_away_club_elo
                        )
                        new_player_elo = player_analysis.new_elo(team_change)
                        player_elo_updates.append(
                            (player_id, game_analysis.season, new_player_elo)
                        )

            return game_id, game_date, player_elo_updates

        except Exception as e:
            logging.error(f"Error processing game {game_id}: {e}", exc_info=True)
            return None

    def update_elo_with_multiprocessing(self, db_config, games_to_process):
        """
        Parallel processing of games using multiprocessing with chunked updates.

        @param db_config:
        @param games_to_process:
        @return: None
        """
        logging.info(f"Starting ELO update for {len(games_to_process)} games.")
        logging.info(f"START: {games_to_process[0]} - END: {games_to_process[-1]}")

        # List to store all updates
        all_player_elo_updates = []

        # Split len(games_to_process) to BATCH_SIZEd lists
        batches = [
            games_to_process[i : i + self.BATCH_SIZE]
            for i in range(0, len(games_to_process), self.BATCH_SIZE)
        ]

        # Deal with each batch
        for batch in batches:
            if self.games_processed >= self.MAX_GAMES_TO_PROCESS:
                # Exit after processing MAX GAMES
                logging.info(f"Processed {self.games_processed} games. Exiting...")
                return

            with Pool(processes=4) as pool:
                # Adjust the number of processes
                results = pool.map(
                    partial(self.process_game, db_config=db_config), batch
                )

            for result in results:
                if result:
                    game_id, game_date, player_elo_updates = result

                    all_player_elo_updates.extend(player_elo_updates)
                    self._update_progress(game_date, game_id)
                    self.games_processed += 1

                    # Flush to DB if the batch limit is reached
                    if len(all_player_elo_updates) >= self.PLAYER_BATCH_LIMIT:
                        self._flush_player_elo_updates(all_player_elo_updates)
                        all_player_elo_updates = []

            logging.info(f"Batch completed. Processed {len(batch)} games.")

        # Final flush for any remaining updates
        if all_player_elo_updates:
            self._flush_player_elo_updates(all_player_elo_updates)

    def _flush_player_elo_updates(self, all_player_elo_updates):
        """Flush Player ELO updates

        Args:
            all_player_elo_updates (List): List of updates of players
        """
        logging.info(
            f"Flushing {len(all_player_elo_updates)} player ELO updates to the database."
        )
        try:
            with DatabaseConnection(DATABASE_CONFIG) as conn:
                with conn.cursor() as cur:
                    # Insert/Update players_elo table
                    # Conflict: Update
                    cur.executemany(
                        """
                        INSERT INTO players_elo (player_id, season, elo)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (player_id, season)
                        DO UPDATE SET elo = EXCLUDED.elo;
                        """,
                        all_player_elo_updates,
                    )
                    conn.commit()
        except Exception as e:
            logging.error(f"Error flushing player ELO updates: {e}", exc_info=True)


def update_elo():
    """Main Update Function.
    Logs as well.
    Raises:
        ValueError: _description_
    """
    log_file = "elo_update.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            RotatingFileHandler(log_file, maxBytes=5 * 1024 * 1024, backupCount=5),
            logging.StreamHandler(),  # Remove this if you don't want logs in the console
        ],
    )

    try:
        process_game_num = int(
            input("Enter number of games you want to process (recommended 100+): ")
        )
        if process_game_num <= 0:
            raise ValueError("Number of games must be greater than 0.")
    except ValueError as e:
        logging.error(f"Invalid input: {e}. Exiting...")
        sys.exit(1)

    with DatabaseConnection(DATABASE_CONFIG) as conn:
        with conn.cursor() as cur:

            elo_updater = EloUpdater(cur, max_games_to_process=process_game_num)
            games_to_process = elo_updater.fetch_games_to_process()
            elo_updater.update_elo_with_multiprocessing(
                DATABASE_CONFIG, games_to_process
            )


# Main execution
if __name__ == "__main__":
    update_elo()
