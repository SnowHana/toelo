import json
from datetime import datetime
from typing import Dict, List, Tuple

from psycopg import sql

from footy.player_elo.database_connection import DatabaseConnection, DATABASE_CONFIG

# Typing
ClubGoals = Dict[int, List[int]]
PlayersPlayTimes = Dict[Tuple[int, int], Tuple[int, int]]
MatchImpacts = Dict[Tuple[int, int], int]
ClubPlayers = Dict[int, List[int]]


class GameAnalysis:
    """
    Analysis of a single Game (Game ID), including team ratings, player performance, and goal impact.
    """

    FULL_GAME_MINUTES = 90
    DEFAULT_ELO = 1500

    def __init__(self, cur, game_id: int):
        """
        Initialize the GameAnalysis instance for a specific game

        @param cur: Database cursor for executing SQL queries.
        @param game_id: ID of the game being analyzed.
        @raise ValueError: If no home/away clubs are found for the game.
        """
        self._players_play_times = {}
        self._players = {}
        self._match_impact_players = None
        self._club_ratings = None
        self._date = None
        self._season = None

        self.cur = cur
        self.game_id = game_id

        # Fetch all game-related data in bulk
        self._fetch_bulk_game_data()

    def _fetch_bulk_game_data(self):
        """
        Fetch all game-related data in bulk to minimize the number of queries.
        (game_details, players_and_playtimes, goals, player_elos)
        @return: None
        """
        self._fetch_game_details()
        self._fetch_players_and_playtimes()
        self._fetch_goals()
        self._fetch_player_elos()

    def _fetch_game_details(self):
        """
        Fetch game data like: home/away club IDs and game date.
        Also initializes players and goals dictionaries.

        @return: None
        @raise ValueError: If no valid game is found for the given game_id.
        @raise ValueError: If no valid game is found for the given game_id
        """
        self.cur.execute(
            """
            SELECT g.home_club_id, g.away_club_id, g.date
            FROM valid_games g
            WHERE g.game_id = %s
        """,
            (self.game_id,),
        )
        result = self.cur.fetchone()

        # Error: No club found for game id.
        if not result:
            raise ValueError(f"No clubs found for game_id={self.game_id}")
        self.home_club_id, self.away_club_id, game_date = result

        # Some formatting and initialising.
        self._date = datetime.strptime(str(game_date), "%Y-%m-%d")
        self._season = self._date.year

    def _fetch_players_and_playtimes(self):
        """
        Fetch starting players, substitutios,
        `_players` and `_players_play_times` attributes set.

        @return: None
        """
        # Init.
        self._players = {self.home_club_id: [], self.away_club_id: []}
        self._players_play_times = {}

        # Fetch starting players
        self.cur.execute(
            """
            SELECT player_club_id AS club_id, player_id, minutes_played
            FROM appearances
            WHERE game_id = %s
        """,
            (self.game_id,),
        )
        players_playtimes_data = self.cur.fetchall()

        # Fetch substituted players
        self.cur.execute(
            """
            SELECT club_id, player_id, player_in_id, minute
            FROM game_events
            WHERE type = 'Substitutions' AND game_id = %s
        """,
            (self.game_id,),
        )
        substitutions_data = self.cur.fetchall()

        # Process starting players
        for club_id, player_id, minutes_played in players_playtimes_data:
            if player_id is not None:
                self._players.setdefault(club_id, []).append(player_id)
                end_time = (
                    minutes_played if minutes_played > 0 else self.FULL_GAME_MINUTES
                )
                self._players_play_times[(club_id, player_id)] = (0, end_time)

        # Process substituted players
        for club_id, player_id, player_in_id, minute in substitutions_data:
            if (
                player_id is not None
                and (club_id, player_id) in self._players_play_times
            ):
                self._players_play_times[(club_id, player_id)] = (
                    self._players_play_times[(club_id, player_id)][0],
                    minute,
                )
            if player_in_id is not None:
                self._players_play_times[(club_id, player_in_id)] = (
                    minute,
                    self.FULL_GAME_MINUTES,
                )
                self._players.setdefault(club_id, []).append(player_in_id)

        # Add players_list field
        self._players_list = [
            player for club_players in self._players.values() for player in club_players
        ]

    def _fetch_goals(self):
        """
        Fetch goal events during the game
        `_goals_per_club` set

        @return: None
        """
        # Init.
        self._goals_per_club = {self.home_club_id: [], self.away_club_id: []}

        self.cur.execute(
            """
            SELECT club_id, minute
            FROM game_events
            WHERE type = 'Goals' AND game_id = %s
        """,
            (self.game_id,),
        )
        goals_data = self.cur.fetchall()

        for club_id, minute in goals_data:
            self._goals_per_club.setdefault(club_id, []).append(minute)

    def _fetch_player_elos(self):
        """
        Fetch ELO ratings for all players involved in the game.
        For players with no existing ELO, estimate their ELO based on teammates or use the default ELO.

        @return: None
        """
        if not self.players_list:
            self._elos = {}
            return

        # Fetch ELOs in bulk
        query = sql.SQL(
            """
            SELECT player_id, elo FROM players_elo
            WHERE player_id IN ({ids}) AND season = %s
        """
        ).format(ids=sql.SQL(", ").join(sql.Placeholder() * len(self.players_list)))
        self.cur.execute(query, (*self.players_list, self.season))
        elos_data = self.cur.fetchall()
        elos_dict = dict(elos_data)

        # Process ELOs
        self._elos = {}
        for player_id in self._players_list:
            elo = elos_dict.get(player_id)
            if elo is not None:
                self._elos[player_id] = elo
            else:
                club_id = next(
                    (
                        cid
                        for cid, players in self.players.items()
                        if player_id in players
                    ),
                    None,
                )
                if club_id:
                    teammate_elos = [
                        self._elos[pid]
                        for pid in self.players[club_id]
                        if pid in self._elos
                    ]
                    self._elos[player_id] = (
                        sum(teammate_elos) / len(teammate_elos)
                        if teammate_elos
                        else self.DEFAULT_ELO
                    )
                else:
                    self._elos[player_id] = self.DEFAULT_ELO

    def _fetch_match_impact_players(self) -> MatchImpacts:
        """
        Calculate the match impact of all players who participated in this game.

        @return: MatchImpacts = Dict[Tuple[int, int], int] = {(club_id, player_id) : player_goal_impacts}
        A dictionary containing the impact of each player, measured by goals scored minus goals conceded.
        """
        goal_minutes = self._goals_per_club
        play_times = self._players_play_times
        player_goal_impacts = {}

        for (club_id, player_id), (start_time, end_time) in play_times.items():
            goals_scored = sum(
                1
                for minute in goal_minutes.get(club_id, [])
                if start_time <= minute <= end_time
            )
            goals_conceded = sum(
                1
                for opp_club_id, opp_minutes in goal_minutes.items()
                if opp_club_id != club_id
                and any(start_time <= minute <= end_time for minute in opp_minutes)
            )
            player_goal_impacts[(club_id, player_id)] = goals_scored - goals_conceded
        return player_goal_impacts

    def _calculate_club_ratings(self) -> Dict[int, float]:
        """
        Calculate the average ELO rating for each team based on player participation.

        @return Dict[int, float]: Dictionary of club ratings {clubID: avgClubELO}.

        @warning Logs a warning if no players are found for a club.
        """
        total_rating = {self.home_club_id: 0, self.away_club_id: 0}
        total_playtime = {self.home_club_id: 0, self.away_club_id: 0}

        for club_id in [self.home_club_id, self.away_club_id]:
            # Check key exists in players
            if club_id not in self.players:
                raise ValueError(f"Warning: No players found for club_id={club_id}.")

            players = self.players.get(club_id, [])
            for player_id in players:
                # Check key exists in players play times
                if (club_id, player_id) not in self.players_play_times:
                    raise ValueError(
                        f"Warning: No player found from player play time record Club: {club_id}"
                        f", Player: {player_id}"
                    )

                start, end = self.players_play_times.get((club_id, player_id), (0, 0))
                minutes_played = abs(end - start)
                if start == 90:
                    minutes_played = 1
                # Check player exist in ELO
                if player_id not in self.elos:
                    raise ValueError(
                        f"Warning: No player found from ELO with player ID {player_id}."
                    )
                # player_elo = self.elos.get(player_id, 0.0)
                player_elo = self.elos[player_id]

                # Calculate
                total_rating[club_id] += minutes_played * player_elo
                total_playtime[club_id] += minutes_played

        club_ratings = {}
        for club_id in (self.home_club_id, self.away_club_id):
            if total_playtime[club_id] > 0:
                club_ratings[club_id] = total_rating[club_id] / total_playtime[club_id]
            else:
                # Play time is 0...related to dataset being incomplete. Return defualt ELO?
                club_ratings[club_id] = self.DEFAULT_ELO

        return club_ratings

    @property
    def date(self) -> datetime:
        """
        Get the date of the game.

        @return: The date of the game.
        """
        return self._date

    @property
    def season(self) -> int:
        """
        Get the season (year) of the game.

        @return: The year of the game.
        """
        return self._season

    @property
    def club_ratings(self) -> Dict[int, float]:
        """
        Get the ratings of the home and away clubs.

        @return: A dictionary containing the ratings of both clubs.
        """
        if self._club_ratings is None:
            self._club_ratings = self._calculate_club_ratings()
        return self._club_ratings

    @property
    def goals_per_club(self) -> ClubGoals:
        """
        Get the goals scored by each club.

        @return: A dictionary containing lists of goal minutes for each club.
        """
        return self._goals_per_club

    @property
    def players_play_times(self) -> PlayersPlayTimes:
        """
        Get the play times of players in the game.

        @return: A dictionary containing the start and end times of each player's participation.
        """
        return self._players_play_times

    @property
    def players(self) -> ClubPlayers:
        """
        Get the players for each club in the game.

        @return: A dictionary containing lists of player IDs for each club.
        """
        return self._players

    @property
    def elos(self) -> Dict[int, float]:
        """
        Get the ELO ratings of players in the game.

        @return: A dictionary containing the ELO ratings of each player.
        """
        return self._elos

    @property
    def players_list(self) -> List[int]:
        """
        Get list of players (In a single List)
        @return: Single list of all players in this game
        """

        return self._players_list

    @property
    def match_impact_players(self) -> MatchImpacts:
        """
        Get the match impact for all players who participated in the game.

        @return: A dictionary containing the impact of each player, measured by goals scored minus goals conceded.
        """
        if self._match_impact_players is None:
            self._match_impact_players = self._fetch_match_impact_players()
        return self._match_impact_players

    def summary(self) -> Dict[str, any]:
        """
        Generate a summary of key attributes and properties.

        @return: A dictionary containing a summary of the game analysis.
        """
        return {
            "game_id": self.game_id,
            "home_club_id": self.home_club_id,
            "away_club_id": self.away_club_id,
            "club_ratings": self.club_ratings,
            "goals_per_club": self.goals_per_club,
            "players_play_times": self.players_play_times,
            "players": self.players,
            "elos": self.elos,
        }

    def print_summary(self):
        """
        Print a formatted summary of key attributes and properties.
        """
        summary = self.summary()
        for key, value in summary.items():
            print(f"{key}: {value}")

    def save_summary_to_json(self, filename: str = "game_analysis_summary.json"):
        """
        Save a summary of key attributes and properties to a JSON file.

        @param filename: The name of the JSON file to save the summary to.
        """
        summary = self.summary()
        with open(filename, "w") as file:
            json.dump(summary, file, indent=4)
        print(f"Summary saved to {filename}")


if __name__ == "__main__":
    with DatabaseConnection(DATABASE_CONFIG) as conn:
        with conn.cursor() as cur:
            # Initialize game-level analysis
            # game_analysis = GameAnalysis(cur, game_id=2331123)
            game_analysis = GameAnalysis(cur, game_id=2287203)
            game_analysis.print_summary()
