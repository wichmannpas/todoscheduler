from datetime import date


class Day:
    """A day class for advanced day functionality."""
    def __init__(self, user, day):
        self.user = user
        self.day = day
        self.executions = []

    def __eq__(self, other):
        return self.day == other.day

    def __hash__(self):
        return hash(self.day)

    def in_past(self) -> bool:
        return self.day < date.today()

    def is_today(self) -> bool:
        today = date.today()
        return self.day == today
