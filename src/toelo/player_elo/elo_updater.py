import logging
import logging.config
from logging.handlers import RotatingFileHandler
import sys
from multiprocessing import Pool
from pathlib import Path

from toelo.player_elo.club_analysis import ClubAnalysis
from toelo.player_elo.database_connection import DATABASE_CONFIG, get_engine
from toelo.player_elo.game_analysis import GameAnalysis
from toelo.player_elo.player_analysis import PlayerAnalysis
from sqlalchemy import text

# Add the src directory to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_PROCESS_NUM = 4
sys.path.append(str(BASE_DIR))

# ==== Logging ====
log_file = "elo_update.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s- %(levelname)s - %(message)s",
    handlers=[
        RotatingFileHandler(log_file, maxBytes=5 * 1024 * 1024, backupCount=5),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

global_engine = None


def init_worker_process(db_config=DATABASE_CONFIG):
    """Initialiser for each worker process....
    Here it simply creates a global engine
    Args:
        db_config (_type_, optional): _description_. Defaults to DATABASE_CONFIG.
    """
    global global_engine
    global_engine = get_engine(db_config)


class EloUpdater:
    """Class for updating ELOs based on game data."""

    BATCH_SIZE = 100  # Number of games processed per batch
    PLAYER_BATCH_LIMIT = 1000  # Maximum player ELO updates before flushing

    def __init__(self, conn, max_games_to_process=1000):
        """Initialise EloUpdater Class
        that handles entire elo analysing, updating.

        Args:
            conn (_type_): engine.connect()
            max_games_to_process (int, optional): _description_. Defaults to 1000.
        """
        self.conn = conn
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
        result = self.conn.execute(
            text(
                """
            SELECT last_processed_date, last_processed_game_id
            FROM process_progress
            WHERE process_name = 'elo_update';
        """
            )
        ).fetchone()

        return result if result else (None, None)

    def _update_progress(self, last_game_date: str, last_game_id: int) -> None:
        """
        Update and commit the progress tracker with the last processed game date and game ID
        @param last_game_date: Date of the last processed game
        @param last_game_id: ID of last processed game ID

        @return: None
        """
        self.conn.execute(
            text(
                """
            UPDATE process_progress
            SET last_processed_date = :game_date, last_processed_game_id = :game_id
            WHERE process_name = 'elo_update';
        """
            ),
            {"game_date": last_game_date, "game_id": last_game_id},
        )
        # self.conn.commit()

    def fetch_games_to_process(self):
        """
        Fetch the list of games to process.
        @return: List of games to process (game_id, date) of valid games
        """
        last_processed_date, last_processed_game_id = self._get_last_processed_game()

        if last_processed_date:
            # Count and log remaining games to process
            count_result = self.conn.execute(
                text(
                    """
                    SELECT COUNT(*) FROM valid_games
                    WHERE (date::DATE >  :last_date OR (date::DATE = :last_date AND game_id > :last_game_id));
                    """
                ),
                {
                    "last_date": last_processed_date,
                    "last_game_id": last_processed_game_id,
                },
            ).fetchone()
            logger.info(f"Remaining games to analyse: {count_result[0]}")

            # Bulk-fetch batch sized games data
            result = self.conn.execute(
                text(
                    """
                    SELECT game_id, date 
                    FROM valid_games 
                    WHERE (date::DATE > :last_date OR (date::DATE = :last_date AND game_id > :last_game_id))
                    ORDER BY date, game_id ASC
                    LIMIT :limit;
                """
                ),
                {
                    "last_date": last_processed_date,
                    "last_game_id": last_processed_game_id,
                    "limit": self.MAX_GAMES_TO_PROCESS,
                },
            ).fetchall()
        else:
            count_result = self.conn.execute(
                text("SELECT COUNT(*) FROM valid_games;")
            ).fetchone()
            logger.info(f"Remaining games to analyse: {count_result[0]}")
            result = self.conn.execute(
                text(
                    """
                    SELECT game_id, date 
                    FROM valid_games 
                    ORDER BY date, game_id ASC
                    LIMIT :limit;
                """
                ),
                {"limit": self.MAX_GAMES_TO_PROCESS},
            ).fetchall()

        return result

    @staticmethod
    def process_game(game):
        """
        Static method to process a SINGLE game and return player ELO updates.

        @param game: (game_id, game_date)
        @param db_config: Database Config
        @return: Tuple (game_id, game_date, player_elo_updates) or None if there's an error
        """
        global global_engine
        game_id, game_date = game
        player_elo_updates = []
        try:
            # Each process opens its own database connection
            # engine = get_engine(db_config)
            # with DatabaseConnection(db_config) as conn:
            with global_engine.connect() as conn:
                # logger.info(f"Processing game {game_id} on date {game_date}")

                game_analysis = GameAnalysis(conn=conn, game_id=game_id)

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
                        logger.error(
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
            logger.error(f"Error processing game {game_id}: {e}", exc_info=True)
            return None

    def update_elo_with_multiprocessing(self, db_config, games_to_process):
        """
        Parallel processing of games using multiprocessing with chunked updates.

        @param db_config:
        @param games_to_process:
        @return: None
        """
        logger.info(f"Starting ELO update for {len(games_to_process)} games.")
        logger.info(f"START: {games_to_process[0]} - END: {games_to_process[-1]}")

        # List to store all updates
        all_player_elo_updates = []
        # Split len(games_to_process) to BATCH_SIZEd lists
        batches = [
            games_to_process[i : i + self.BATCH_SIZE]
            for i in range(0, len(games_to_process), self.BATCH_SIZE)
        ]

        # Create a pool that initializes each worker with the shared engine.
        with Pool(
            processes=DEFAULT_PROCESS_NUM,
            initializer=init_worker_process,
            initargs=(db_config,),
        ) as pool:
            for batch in batches:
                if self.games_processed >= self.MAX_GAMES_TO_PROCESS:
                    logger.info(f"Processed {self.games_processed} games. Exiting...")
                    return

                results = pool.map(self.process_game, batch)

                for result in results:
                    if result:
                        game_id, game_date, player_elo_updates = result
                        # logger.info(f"UPDATE: Updating {game_id} on {game_date}.")
                        all_player_elo_updates.extend(player_elo_updates)
                        self._update_progress(game_date, game_id)
                        # logger.info(
                        #     f"UPDATE COMPLETE: Updated {game_id} on {game_date}."
                        # )
                        self.games_processed += 1

                        if len(all_player_elo_updates) >= self.PLAYER_BATCH_LIMIT:
                            self._flush_player_elo_updates(all_player_elo_updates)
                            all_player_elo_updates = []

                logger.info(f"Batch completed. Processed {len(batch)} games.")

        if all_player_elo_updates:
            self._flush_player_elo_updates(all_player_elo_updates)

    def _flush_player_elo_updates(self, all_player_elo_updates):
        """Flush Player ELO updates
        This will be ran only one time...
        Args:
            all_player_elo_updates (List): List of updates of players
        """
        logger.info(
            f"Flushing {len(all_player_elo_updates)} player ELO updates to the database."
        )

        global global_engine
        try:
            # with DatabaseConnection(DATABASE_CONFIG) as conn::
            # Insert/Update players_elo table
            # Conflict: Update
            self.conn.execute(
                text(
                    """
                    INSERT INTO players_elo (player_id, season, elo)
                    VALUES (:player_id, :season, :elo)
                    ON CONFLICT (player_id, season)
                    DO UPDATE SET elo = EXCLUDED.elo;
                    """
                ),
                [
                    {"player_id": update[0], "season": update[1], "elo": update[2]}
                    for update in all_player_elo_updates
                ],
            )
        except Exception as e:
            logger.error(f"Error flushing player ELO updates: {e}", exc_info=True)


def update_elo(process_game_num: int):
    """Main Update Function.
    Logs as well.
    Raises:
        ValueError: _description_
    """
    try:
        if process_game_num <= 0:
            raise ValueError("Number of games must be greater than 0.")
        engine = get_engine()
        with engine.begin() as conn:
            elo_updater = EloUpdater(conn, max_games_to_process=process_game_num)
            games_to_process = elo_updater.fetch_games_to_process()
            elo_updater.update_elo_with_multiprocessing(
                DATABASE_CONFIG, games_to_process
            )
    except ValueError as e:
        logger.error(f"Invalid input: {e}. Exiting...")
        sys.exit(1)


def get_progress():
    """Get Progress

    Returns:
        [remaining, total_game]
    """
    engine = get_engine()
    with engine.connect() as conn:
        # Get max
        max_game = conn.execute(
            text("""SELECT COUNT(*) FROM valid_games;""")
        ).fetchone()[0]

        # Rem.
        remaining = 0
        elo_updater = EloUpdater(conn)

        last_processed_date, last_processed_game_id = (
            elo_updater._get_last_processed_game()
        )

        if last_processed_date:
            # Count and log remaining games to process
            count_result = conn.execute(
                text(
                    """
                    SELECT COUNT(*) FROM valid_games
                    WHERE (date::DATE >  :last_date OR (date::DATE = :last_date AND game_id > :last_game_id));
                    """
                ),
                {
                    "last_date": last_processed_date,
                    "last_game_id": last_processed_game_id,
                },
            ).fetchone()
            remaining = count_result[0]
        else:
            count_result = conn.execute(
                text("SELECT COUNT(*) FROM valid_games;")
            ).fetchone()
            remaining = count_result[0]

        # return (int(remaining), int(max_game))
        return [remaining, max_game]


# Main execution
if __name__ == "__main__":
    update_elo()
