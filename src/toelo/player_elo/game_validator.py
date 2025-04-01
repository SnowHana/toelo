from toelo.player_elo.database_connection import get_engine
from sqlalchemy import String, text


class GameValidator:
    """
    Class for validating and selecting valid games.

    Attributes:
        conn: Database connection for creating separate cursors.
    """

    BATCH_SIZE = 10000  # Adjust batch size based on performance

    def __init__(self, engine):
        """
        Initialize the GameValidator class.

        Args:
            engine: Database connection object for creating cursors. SQLalchemy engine
        """
        self.engine = engine
        self._ensure_valid_games_table_exists()

    def _ensure_valid_games_table_exists(self):
        """
        Ensure the `valid_games` table exists in the database.
        If not, create it based on the structure of the `games` table.
        """
        # with self.conn.cursor() as cur:
        with self.engine.begin() as conn:
            try:
                conn.execute(
                    text(
                        """
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1
                        FROM information_schema.tables 
                        WHERE table_schema = 'public' AND table_name = 'valid_games'
                    ) THEN
                        CREATE TABLE public.valid_games AS
                        SELECT * FROM public.games WHERE 1 = 0;
                        ALTER TABLE public.valid_games ADD CONSTRAINT valid_games_game_id_pk PRIMARY KEY (game_id);
                    END IF; 
                END
                $$;
            """
                    )
                )
                print("Ensured `valid_games` table exists.")
            except Exception as e:
                print(f"Error occured while ensuring 'valid_games' table exists: {e}")

    def _fetch_game_ids_batch(self):
        """
        Generator to fetch game IDs in batches.

        Yields:
            list: A batch of game IDs.
        """
        with self.engine.connect() as conn:
            res = conn.execute(text("SELECT game_id FROM games ORDER BY game_id;"))
            all_rows = res.fetchall()
            # while True:
            #     batch = res.fetchmany(self.BATCH_SIZE)
            #     if not batch:
            #         break
            #     yield [row[0] for row in batch]
        for i in range(0, len(all_rows), self.BATCH_SIZE):
            yield [row[0] for row in all_rows[i : i + self.BATCH_SIZE]]

    def _validate_and_insert_games(self, game_ids):
        """
        Use SQL to validate and insert valid games into `valid_games`.

        Args:
            game_ids (list): List of game IDs to validate and insert.
        """
        # return
        with self.engine.begin() as conn:
            try:
                # with self.conn.cursor() as cur:

                conn.execute(
                    text(
                        """
                        WITH valid_games_batch AS (
                            SELECT g.*
                            FROM games g
                            WHERE g.game_id = ANY(:x)
                                AND EXISTS (
                                    SELECT 1
                                    FROM appearances a
                                    WHERE a.game_id = g.game_id
                                )
                        )
                        INSERT INTO valid_games
                        SELECT * FROM valid_games_batch
                        ON CONFLICT (game_id) DO NOTHING;
                        """
                    ),
                    {"x": game_ids},
                )

                print(f"Validated and inserted batch of {len(game_ids)} games.")
            except Exception as e:
                print(f"Error validating / inserting games: {e}")

    def add_valid_games(self):
        """
        Process the Games table in batches, validate games, and add valid games to the `valid_games` table.
        """
        print("Starting validation...")

        for batch_game_ids in self._fetch_game_ids_batch():
            self._validate_and_insert_games(batch_game_ids)

        print("Validation complete.")


def validate_games():
    # with get_engine() as engine:
    engine = get_engine()
    validator = GameValidator(engine=engine)
    validator.add_valid_games()


# Usage
if __name__ == "__main__":
    validate_games()
