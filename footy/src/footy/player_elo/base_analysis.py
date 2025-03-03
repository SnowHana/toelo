# from .elo_calculation_mixin import ELOCalculationMixin
from abc import abstractmethod
from typing import Dict

from footy.player_elo.game_analysis import GameAnalysis


class BaseAnalysis:
    """
    Base class providing common ELO calculation and expectation methods for both Club and Player analysis.
    @todo: Decide like what exactly this class should do?
    """

    MINUTES_MAX = 90

    def __init__(
        self,
        game_analysis: GameAnalysis,
        entity_id: int,
        k_value: float,
        q_value: float,
        weight: float = 1,
    ):
        """
        Initialize.

        @param k_value:
        @param q_value:
        @param game_analysis: Instance of GameAnalysis providing game context
        @param entity_id: ID of the entity (club or player) to analyze
        @param is_club: Boolean indicating if the entity is a club (True) or a player (False)
        """
        self.q_value = q_value
        self.k_value = k_value
        self.game_analysis = game_analysis
        self.entity_id = entity_id
        self.weight = weight

        # Lazy Loaded fields
        self._elo = None
        self._minutes_played = None
        self._goal_difference = None
        # Get opponent club id because it's useful for both Club and Player Analysis
        self._opponent_id = None
        # Below are values that is being calculated in this fn.
        self._game_score = None
        self._expectation = None
        # self._elo_change = None

    @abstractmethod
    def _fetch_elo(self) -> float:
        """
        Retrieve or calculate the ELO for the entity (club or player).
        """

    @abstractmethod
    def _calculate_expectation(self) -> float:
        """
        Calculate the expected performance based on ELO ratings.
        """

    @abstractmethod
    def _get_goal_difference(self) -> int:
        """
        Retrieve goal difference for clubs or match impact for players.
        """

    @abstractmethod
    def _get_minutes_played(self) -> int:
        """
        Get the minutes played by the player or return full game duration for clubs.
        """

    @abstractmethod
    def _get_opponent_id(self) -> int:
        """
        Get Opponent Club ID of the Entity (Club / Player)
        """

    @property
    def elo(self) -> float:
        if self._elo is None:
            self._elo = self._fetch_elo()
        return self._elo

    @property
    def expectation(self) -> float:
        if self._expectation is None:
            self._expectation = self._calculate_expectation()
        return self._expectation

    @property
    def minutes_played(self) -> int:
        if self._minutes_played is None:
            self._minutes_played = self._get_minutes_played()
        return self._minutes_played

    @property
    def game_score(self) -> float:
        if self._game_score is None:
            self._game_score = self.calculate_game_score()
        return self._game_score

    @property
    def goal_difference(self) -> int:
        if self._goal_difference is None:
            self._goal_difference = self._get_goal_difference()
        return self._goal_difference

    @property
    def opponent_id(self) -> int:
        if self._opponent_id is None:
            self._opponent_id = self._get_opponent_id()
        return self._opponent_id

    def update_elo(self, actual_score: float, weight: float) -> float:
        """
        Update the entity's ELO based on actual performance vs. expected.
        """
        expected_score = self.expectation
        goal_difference = self._get_goal_difference()
        change = self.calculate_change(
            expectation=expected_score,
            game_score=actual_score,
            weight=weight,
            goal_difference=goal_difference,
            minutes_played=self._get_minutes_played(),
        )
        self._elo += change
        return self._elo

    # @staticmethod
    def calculate_game_score(self) -> float:
        """
        Calculate Game Score based on match impact (goal difference).
        @todo : Think about using goal_difference or sth else
        """
        if self.goal_difference > 0:
            return 1.0
        elif self.goal_difference == 0:
            return 0.5
        else:
            return 0.0

    def calculate_change(self) -> float:
        """
        @todo Done, but need to get tested
        Calculate the change in score.
        """
        res = self.weight * (self.game_score - self.expectation)
        if self.goal_difference == 0:
            res *= self.minutes_played / self.MINUTES_MAX
        else:
            res *= abs(self.goal_difference) ** (1 / 3)
        return res

    @abstractmethod
    def new_elo(self) -> float:
        """
        Calculate R'_{A_i}
        @return: New ELO based on our algorithm
        """
        # new_elo = self.elo + self.k_value * ((self.q_value * ))

    def summary(self) -> Dict[str, any]:
        """
        Generate a summary of key attributes and properties for easy viewing during testing.

        @return: Dictionary summarizing the GameAnalysis instance.
        """
        return {
            "elo": self.elo,
            "expectation": self.expectation,
            "game_score": self.game_score,
        }

    def print_summary(self):
        """
        Print a formatted summary of key attributes and properties for easy testing and debugging.
        """
        summary = self.summary()
        for key, value in summary.items():
            print(f"{key}: {value}")
