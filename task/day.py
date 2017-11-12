from datetime import date

from decimal import Decimal


class Day:
    """A day class for advanced day functionality."""
    def __init__(self, user, day):
        self.user = user
        self.day = day
        self.executions = []

    def __eq__(self, other):
        return self.user == other.user and self.day == other.day

    def __hash__(self):
        return hash(self.day) ^ hash(self.user)

    def in_past(self) -> bool:
        return self.day < date.today()

    def is_today(self) -> bool:
        today = date.today()
        return self.day == today

    def is_weekday(self) -> bool:
        return self.day.weekday() < 5

    @property
    def scheduled_duration(self) -> Decimal:
        return Decimal(sum(execution.duration for execution in self.executions))

    @property
    def available_duration(self) -> Decimal:
        return self.max_duration - self.scheduled_duration

    @property
    def max_duration(self) -> Decimal:
        if self.is_weekday():
            return self.user.workhours_weekday
        return self.user.workhours_weekend
