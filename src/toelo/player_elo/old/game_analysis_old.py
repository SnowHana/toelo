# import json
# from datetime import datetime
# from typing import Dict, List, Tuple

# from src.player_elo.database_connection import DatabaseConnection, DATABASE_CONFIG

# # Typing
# ClubGoals = Dict[int, List[int]]
# PlayersPlayTimes = Dict[Tuple[int, int], Tuple[int, int]]
# MatchImpacts = Dict[Tuple[int, int], int]
# Players = Dict[int, List[int]]


# class GameAnalysis:
#     """
#     Analysis of a single Game (Game ID), including team ratings, player performance, and goal impact.

#     @param
#         cur: Database cursor for executing SQL queries.
#         game_id: ID of the game being analyzed.
#         weight: Weight assigned to this game for analysis (default 1).
#         home_club_id: ID of the home club in the game.
#         away_club_id: ID of the away club in the game.
#     """

#     FULL_GAME_MINUTES = 90
#     DEFUALT_ELO = 1500

#     def __init__(self, cur, game_id: int):
#         """
#         Initialize the GameAnalysis instance for a specific game.

#         Args:
#             cur: Database cursor for executing SQL queries.
#             game_id (int): ID of the game being analyzed.

#         Raises:
#             ValueError: If no home/away clubs are found for the game.
#         """
#         self.cur = cur
#         self.game_id = game_id

#         self.home_club_id, self.away_club_id = self._fetch_club_ids()

#         # Players
#         self._players = None

#         # Elos
#         self._elos = None

#         # Lazy-loaded attributes
#         self._club_ratings = None
#         self._goals_per_club = None
#         self._players_play_times = None
#         self._match_impact_players = None
#         self._date = None
#         self._season = None

#         # Optional attributes
#         self._club_elo_change = None

#     def _fetch_club_ids(self) -> Tuple[int, int]:
#         """
#         Retrieve the home and away club IDs for the game.

#         Returns:
#             Tuple[int, int]: Home and away club IDs.

#         Raises:
#             ValueError: If no clubs are found for the game.
#         """
#         self.cur.execute("""
#             SELECT g.home_club_id, g.away_club_id
#             FROM valid_games g
#             WHERE g.game_id = %s
#         """, (self.game_id,))
#         result = self.cur.fetchone()
#         if not result:
#             raise ValueError(f"No clubs found for game_id={self.game_id}")
#         return result

#     def _calculate_club_ratings(self) -> Dict[int, float]:
#         """
#         Calculate the average ELO rating for each team based on player participation.

#         Returns:
#             Dict[int, float]: Dictionary of club ratings {clubID: avgClubELO}.

#         Warnings:
#             Logs a warning if no players are found for a club.
#         """
#         total_rating = {self.home_club_id: 0, self.away_club_id: 0}
#         total_playtime = {self.home_club_id: 0, self.away_club_id: 0}

#         for club_id in [self.home_club_id, self.away_club_id]:
#             # Check key exists in players
#             if club_id not in self.players:
#                 raise ValueError(f"Warning: No players found for club_id={club_id}.")

#             players = self.players.get(club_id, [])
#             for player_id in players:
#                 # Check key exists in players play times
#                 if (club_id, player_id) not in self.players_play_times:
#                     raise ValueError(f"Warning: No player found from player play time record Club: {club_id}"
#                                      f", Player: {player_id}")

#                 start, end = self.players_play_times.get((club_id, player_id), (0, 0))
#                 minutes_played = abs(end - start)
#                 if start == 90:
#                     minutes_played = 1
#                 # Check player exist in ELO
#                 if player_id not in self.elos:
#                     raise ValueError(f"Warning: No player found from ELO with player ID {player_id}.")
#                 # player_elo = self.elos.get(player_id, 0.0)
#                 player_elo = self.elos[player_id]

#                 # Calculate
#                 total_rating[club_id] += minutes_played * player_elo
#                 total_playtime[club_id] += minutes_played

#         club_ratings = {}
#         for club_id in (self.home_club_id, self.away_club_id):
#             if total_playtime[club_id] > 0:
#                 club_ratings[club_id] = total_rating[club_id] / total_playtime[club_id]
#             else:
#                 # Play time is 0...related to dataset being incomplete. Return defualt ELO?
#                 club_ratings[club_id] = self.DEFUALT_ELO

#         return club_ratings

#         # return {
#         #     club_id: total_rating[club_id] / total_playtime[club_id]
#         #     for club_id in (self.home_club_id, self.away_club_id) if total_playtime[club_id] > 0
#         # }

#     def _fetch_goals_per_club(self) -> ClubGoals:
#         """
#         Retrieve goals scored by each club in the game.

#         Returns:
#             ClubGoals: Dictionary mapping club ID to a list of goal-scoring minutes {clubID: [minutes]}.
#         """
#         self.cur.execute("""
#             SELECT club_id, minute
#             FROM game_events
#             WHERE type = 'Goals' AND game_id = %s
#         """, (self.game_id,))

#         goals_by_club = {self.home_club_id: [], self.away_club_id: []}
#         for club_id, minute in self.cur.fetchall():
#             goals_by_club.setdefault(club_id, []).append(minute)
#         return goals_by_club

#     def _fetch_players_play_times(self) -> PlayersPlayTimes:
#         """
#         Retrieve playing times for each player in the game.

#         Returns:
#             PlayersPlayTimes: Dictionary mapping (club_id, player_id) to (start_min, end_min).
#         """
#         self.cur.execute("""
#             SELECT player_club_id AS club_id, player_id, minutes_played
#             FROM appearances
#             WHERE game_id = %s
#         """, (self.game_id,))

#         starting_players = {}
#         for club_id, player_id, minutes_played in self.cur.fetchall():
#             end_time = minutes_played if minutes_played > 0 else self.FULL_GAME_MINUTES
#             starting_players[(club_id, player_id)] = (0, end_time)

#         self.cur.execute("""
#             SELECT club_id, player_id, player_in_id, minute
#             FROM game_events
#             WHERE type = 'Substitutions' AND game_id = %s
#         """, (self.game_id,))

#         play_time = starting_players.copy()
#         for club_id, player_id, player_in_id, minute in self.cur.fetchall():
#             if (club_id, player_id) in play_time:
#                 play_time[(club_id, player_id)] = (play_time[(club_id, player_id)][0], minute)
#             play_time[(club_id, player_in_id)] = (minute, self.FULL_GAME_MINUTES)
#         return play_time

#     def _fetch_players(self) -> Players:
#         """
#         Retrieve players for each club participating in the game.

#         Returns:
#             Players: Dictionary mapping club_id to a list of player_ids {clubID: [playerID]}.
#         """
#         self.cur.execute("""
#             SELECT player_club_id AS club_id, player_id
#             FROM appearances
#             WHERE game_id = %s
#         """, (self.game_id,))

#         players = {self.home_club_id: [], self.away_club_id: []}
#         for club_id, player_id in self.cur.fetchall():
#             players.setdefault(club_id, []).append(player_id)

#         self.cur.execute("""
#             SELECT club_id, player_in_id
#             FROM game_events
#             WHERE type = 'Substitutions' AND game_id = %s
#         """, (self.game_id,))

#         for club_id, player_in_id in self.cur.fetchall():
#             players.setdefault(club_id, []).append(player_in_id)
#         return players

#     def _fetch_date(self) -> datetime:
#         """
#         Fetch the date of the game.

#         Returns:
#             datetime: The date of the game.

#         Raises:
#             ValueError: If no date is found for the game.
#         """
#         self.cur.execute("""
#             SELECT date
#             FROM valid_games
#             WHERE game_id = %s
#         """, (self.game_id,))
#         result = self.cur.fetchone()
#         if not result:
#             raise ValueError(f"No date found for game_id={self.game_id}")
#         return datetime.strptime(result[0], "%Y-%m-%d")

#     def _fetch_elos(self) -> Dict[int, float]:
#         """
#         Fetch ELO ratings for all players in the game.

#         Returns:
#             Dict[int, float]: Dictionary mapping player IDs to their ELO ratings {playerID: elo}.
#         """
#         elos = {}
#         for club, players in self.players.items():
#             for player in players:
#                 self.cur.execute("""
#                     SELECT elo FROM players_elo WHERE player_id = %s AND season = %s
#                 """, (player, self.season))
#                 res = self.cur.fetchone()
#                 if res:
#                     # Handle case when we have a matching row, but row contains no data (ie. None)
#                     if res[0] is not None:
#                         elos[player] = res[0]
#                     else:
#                         elos[player] = self.DEFUALT_ELO
#                 else:
#                     # No matching row / res[0] is None
#                     elos[player] = self.DEFUALT_ELO
#                 # elos[player] = res[0] if res else self.DEFUALT_ELO
#         return elos

#     def _fetch_match_impact_players(self) -> MatchImpacts:
#         """
#             Calculate the match impact of all players who participated in this game.

#             @note 'Match Impact': Goal difference while player was on the pitch.
#             @return: MatchImpacts: Dictionary mapping (club_id, player_id) to match impact
#         """
#         goal_minutes = self.goals_per_club
#         play_times = self.players_play_times
#         player_goal_impacts = {}

#         for (club_id, player_id), (start_time, end_time) in play_times.items():
#             goals_scored = sum(1 for minute in goal_minutes.get(club_id, []) if start_time <= minute <= end_time)
#             goals_conceded = sum(1 for opp_club_id, opp_minutes in goal_minutes.items()
#                                  if opp_club_id != club_id and any(
#                 start_time <= minute <= end_time for minute in opp_minutes))
#             player_goal_impacts[(club_id, player_id)] = goals_scored - goals_conceded
#         return player_goal_impacts

#     @property
#     def date(self) -> datetime:
#         if self._date is None:
#             self._date = self._fetch_date()
#         return self._date

#     @property
#     def season(self) -> int:
#         if self._season is None:
#             self._season = self.date.year
#         return self._season

#     @property
#     def club_ratings(self) -> Dict[int, float]:
#         if self._club_ratings is None:
#             self._club_ratings = self._calculate_club_ratings()
#         return self._club_ratings

#     @property
#     def goals_per_club(self) -> ClubGoals:
#         if self._goals_per_club is None:
#             self._goals_per_club = self._fetch_goals_per_club()
#         return self._goals_per_club

#     @property
#     def players_play_times(self) -> PlayersPlayTimes:
#         if self._players_play_times is None:
#             self._players_play_times = self._fetch_players_play_times()
#         return self._players_play_times

#     @property
#     def players(self) -> Players:
#         if self._players is None:
#             self._players = self._fetch_players()
#         return self._players

#     @property
#     def elos(self) -> Dict[int, float]:
#         if self._elos is None:
#             self._elos = self._fetch_elos()
#         return self._elos

#     @property
#     def match_impact_players(self):
#         if self._match_impact_players is None:
#             self._match_impact_players = self._fetch_match_impact_players()
#         return self._match_impact_players

#     def summary(self) -> Dict[str, any]:
#         """
#         Generate a summary of key attributes and properties.

#         Returns:
#             Dict[str, any]: Dictionary summarizing the GameAnalysis instance.
#         """
#         return {
#             "game_id": self.game_id,
#             "home_club_id": self.home_club_id,
#             "away_club_id": self.away_club_id,
#             "club_ratings": self.club_ratings,
#             "goals_per_club": self.goals_per_club,
#             "players_play_times": self.players_play_times,
#             "players": self.players,
#             "elos": self.elos,
#         }

#     def print_summary(self):
#         """
#         Print a formatted summary of key attributes and properties.
#         """
#         summary = self.summary()
#         for key, value in summary.items():
#             print(f"{key}: {value}")

#     def save_summary_to_json(self, filename: str = "game_analysis_summary.json"):
#         """
#         Save a summary of key attributes and properties to a JSON file.

#         Args:
#             filename (str): The name of the JSON file to save the summary.
#         """
#         summary = self.summary()
#         with open(filename, 'w') as file:
#             json.dump(summary, file, indent=4)
#         print(f"Summary saved to {filename}")


# if __name__ == "__main__":
#     with DatabaseConnection(DATABASE_CONFIG) as conn:
#         with conn.cursor() as cur:
#             # Initialize game-level analysis
#             game_analysis = GameAnalysis(cur, game_id=2246172)
#             game_analysis.print_summary()
#         # game_analysis.print_summary()
# #         # game_analysis.save_summary_to_json()
# #         #
# #         # # Analyze overall team performance
# #         # team_performance = game_analysis.analyze_team_performance()
# #         # print("Team Performance:", team_performance)
# #         #
# #         # # Individual player analysis based on shared game data
# #         # player_analytics = PlayerAnalysis(game_analysis, player_id=20506)
# #         # playing_time = player_analytics.playing_time
# #         # print(f"Player {player_analytics.player_id} Playing Time:", playing_time)
# #         #
# #         # expectation = player_analytics.player_expectation
# #         # print(f"Player {player_analytics.player_id} Expectation:", expectation)
# #         pass
