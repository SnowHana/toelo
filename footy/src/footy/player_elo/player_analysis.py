import logging

from footy.player_elo.base_analysis import BaseAnalysis
from footy.player_elo.game_analysis import GameAnalysis


class PlayerAnalysis(BaseAnalysis):
    """
    Analysis specific to player performance, inheriting shared logic from BaseAnalysis.
    """

    def __init__(self, game_analysis: GameAnalysis, player_id: int):
        super().__init__(game_analysis, entity_id=player_id, k_value=32, q_value=1)
        # IDK maybe delete this cuz it's confusing?
        self.player_id = player_id
        self._club_id = None

    @property
    def club_id(self) -> int:
        if self._club_id is None:
            self._club_id = self._get_club_id()
        return self._club_id

    def _fetch_elo(self) -> float:

        try:
            if self.entity_id in self.game_analysis.elos:
                return self.game_analysis.elos[self.entity_id]
            raise KeyError(
                f"Error: Could not find Player {self.entity_id} in Game Analysis ELO record."
            )
        except KeyError as e:
            logging.error(e)
            raise

    def _calculate_expectation(self) -> float:
        opponent_elo = self.game_analysis.club_ratings[self.opponent_id]
        return 1 / (1 + pow(10, (opponent_elo - self.elo) / 400))

    def _get_goal_difference(self) -> int:
        return self.game_analysis.match_impact_players[
            (self._get_club_id(), self.entity_id)
        ]

    def _get_minutes_played(self) -> int:
        start_min, end_min = self.game_analysis.players_play_times[
            (self._get_club_id(), self.entity_id)
        ]
        return end_min - start_min

    def _get_club_id(self) -> int:
        """
        Retrieve the club ID for the player.
        """

        try:
            for club_id, club_players in self.game_analysis.players.items():
                if self.entity_id in club_players:
                    return club_id
            raise KeyError(
                f"Error: Could not find Player {self.entity_id} in game {self.game_analysis.game_id}"
            )
        except KeyError as e:
            logging.error(e)
            raise

    def _get_opponent_id(self) -> int:
        """
        Get Opponent Club's ID
        @todo: Later instead of using player's play time, do sth else, like creating a team data for GameAnalysis?
        @return:
        """
        for club_id, player_id in self.game_analysis.players_play_times.keys():
            if player_id == self.entity_id:
                return club_id

    def new_elo(self, team_elo_change: float) -> float:
        """
        @param: team_elo_change: Team ELO Change (C_A)
        @return:
        """

        return self.elo + self.k_value * (
            (self.q_value * self.calculate_change())
            + (
                (1 - self.q_value)
                * team_elo_change
                * (self.minutes_played / self.MINUTES_MAX)
            )
        )
