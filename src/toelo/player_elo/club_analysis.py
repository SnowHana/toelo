from .base_analysis import BaseAnalysis
from .game_analysis import GameAnalysis


class ClubAnalysis(BaseAnalysis):

    def __init__(self, game_analysis: GameAnalysis, club_id: int):
        super().__init__(game_analysis, entity_id=club_id, k_value=32, q_value=1)

    def _fetch_elo(self) -> float:
        return self.game_analysis.club_ratings.get(self.entity_id, 0)

    def _calculate_expectation(self) -> float:
        opponent_elo = self.game_analysis.club_ratings[self.opponent_id]
        return 1 / (1 + pow(10, (opponent_elo - self.elo) / 400))

    def _get_goal_difference(self) -> int:
        goals_for = len(self.game_analysis.goals_per_club[self.entity_id])
        opponent_id = (
            self.game_analysis.home_club_id
            if self.entity_id == self.game_analysis.away_club_id
            else self.game_analysis.away_club_id
        )
        goals_against = len(self.game_analysis.goals_per_club[opponent_id])
        return goals_for - goals_against

    def _get_minutes_played(self) -> int:
        return self.game_analysis.FULL_GAME_MINUTES

    def _get_opponent_id(self) -> int:
        """
        Get Opponent Club's id
        """
        opponent_id = (
            self.game_analysis.home_club_id
            if self.entity_id == self.game_analysis.away_club_id
            else self.game_analysis.away_club_id
        )
        return opponent_id

    def new_elo(self) -> float:
        """

        Calculate R'_{A_i}
        @return: New ELO for the club based on our algorithm
        """

        return self.elo + 20 * self.calculate_change()
