import logging
from datetime import datetime

from footy.player_elo.club_analysis import ClubAnalysis
from footy.player_elo.database_connection import DatabaseConnection, DATABASE_CONFIG
from footy.player_elo.game_analysis import GameAnalysis
from footy.player_elo.player_analysis import PlayerAnalysis


def process_game(game, db_config):
    """
    Static method to process a single game and return player ELO updates.

    @param game: Tuple containing game_id and game_date
    @param db_config: Database configuration dictionary
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
                # players = [player for club_players_list in game_analysis.players.values() for player in
                #            club_players_list]
                for player_id in game_analysis.players_list:
                    # TODO: We have a case where player_id is null?
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


process_game((2225462, datetime(2012, 9, 23)), DATABASE_CONFIG)
