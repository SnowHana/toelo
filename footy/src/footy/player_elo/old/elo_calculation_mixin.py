# elo_calculation_mixin.py
from __future__ import annotations

from typing import Union

from .player_elo import PlayerAnalysis, GameAnalysis


class ELOCalculationMixin:
    """
    Mixin class providing methods for calculating ELO
    """

    @staticmethod
    def calculate_game_score(analysis: Union[GameAnalysis, PlayerAnalysis]) -> float:
        """
        Calculate Game Score based on match impact (goal difference).
        @param analysis: Game Analysis / Player Analytics
        @param id: Club ID / (Club ID, Player ID)
        @return: Game score
        """

        match_impact = None

        if isinstance(analysis, GameAnalysis):
            # Game Analysis
            # club_id = id
            # opponent_id = analysis.home_club_id if id == analysis.away_club_id else analysis.away_club_id

            home_goals = analysis.goals_per_club[analysis.home_club_id]
            away_goals = analysis.goals_per_club[analysis.away_club_id]

            # Calculating club
            gd = len(home_goals) - len(away_goals)
            match_impact = gd

        elif isinstance(analysis, PlayerAnalysis):
            # Single Player
            # club_id, player_id = id
            match_impact = analysis.match_impact

        if match_impact > 0:
            return 1.0
        elif match_impact == 0:
            return 0.5
        else:
            return 0.0

    @staticmethod
    def calculate_change(analysis: Union[GameAnalysis, PlayerAnalysis]) -> float:
        """
        Calculate the change in score based on player expectation, game score, and weight.

        @param expectation: Player's expected score
        @param game_score: Actual game score
        @param weight: Weighting factor for the change calculation
        @param goal_difference: Goal Difference at the end of the game / player's play
        @param minutes_played:
        @param minutes_max: Maximum Minutes (90)
        @return: Calculated change
        """
        res = weight * (game_score - expectation)
        if goal_difference == 0:
            res *= (minutes_played / minutes_max)
        else:
            res *= (pow(abs(goal_difference), 1 / 3))

        return res
