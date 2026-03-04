"""Scoreline dataclass — adapted from pldashboard scoreline.py."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Scoreline:
    home_goals: int
    away_goals: int

    @property
    def total_goals(self) -> int:
        return self.home_goals + self.away_goals

    @property
    def both_scored(self) -> bool:
        return self.home_goals > 0 and self.away_goals > 0

    @property
    def home_win(self) -> bool:
        return self.home_goals > self.away_goals

    @property
    def away_win(self) -> bool:
        return self.away_goals > self.home_goals

    @property
    def draw(self) -> bool:
        return self.home_goals == self.away_goals

    @property
    def result(self) -> str:
        if self.home_win:
            return "H"
        elif self.away_win:
            return "A"
        return "D"

    def __str__(self) -> str:
        return f"{self.home_goals}-{self.away_goals}"
