# Tools for filtering lists of court availabilities
from datetime import datetime, time, timedelta
from dataclasses import dataclass

from goodminton.courts import CourtAvailability


class InvalidTimeRangeException(Exception):
    """
    An exception to be raised when a time range is incorrectly formatted.
    """

    pass


@dataclass
class TimeRangeFilter:
    """
    Filter (and truncate) availabilities which match a specified time range.
    """

    start: time | None = None
    end: time | None = None

    @classmethod
    def from_str(cls, s: str):
        """
        Derive a time-range filter from a string of the form '%HH:%MM-%HH:%MM'
        in 24hr ISO format. One of the times may be omitted (with dash remaining),
        but not both.

        :param s: The string representation of the time-range, e.g., '13:00-16:00'.
        :type s: str
        """
        start_str, end_str = s.split("-")
        if not end_str:
            end = None
        if not start_str:
            start = None
        try:
            if end_str:
                end = time.fromisoformat(end_str)
            if start_str:
                start = time.fromisoformat(start_str)
        except ValueError as e:
            raise InvalidTimeRangeException(*e.args)
        if end or start:
            return cls(start=start, end=end)
        else:
            raise InvalidTimeRangeException("Must specify either `start` or `end`.")

    def filter(
        self, availabilities: list[CourtAvailability]
    ) -> list[CourtAvailability]:
        """
        Filter a set of availabilities based on time.

        :param availabilities: The list of availabilities to filter.
        :type availabilities: list[CourtAvailability]
        :return: A list of truncated availabilities in the time range.
        :rtype: list[CourtAvailability]
        """
        filtered = []
        for avail in availabilities:
            candidate = CourtAvailability(**avail.__dict__)
            if self.start:
                # Skip if avail ends before filter start
                if self.start > avail.end.time():
                    continue
                # If avail starts before filter start, move start forward.
                if avail.start.time() < self.start:
                    candidate.start = datetime.combine(avail.start.date(), self.start)
            if self.end:
                # Skip if starts after filter ends
                if self.end < avail.start.time():
                    continue
                # If avail ends after filter end, move the end back.
                if avail.end.time() > self.end:
                    candidate.end = datetime.combine(avail.end.date(), self.end)
            # Final sanity check
            if candidate.start < candidate.end:
                filtered.append(candidate)
        return filtered


@dataclass
class DurationFilter:
    """
    Filter availabilities which exceed some minimum duration.
    """

    min_duration: timedelta = timedelta(seconds=60 * 60)

    @classmethod
    def from_str(cls, s: str):
        """
        Derive a duration filter from a string representing the number of hours.

        :param s: A string representing some number of hours, e.g., "0.25".
        :type s: str
        """
        return cls(min_duration=float(s))

    def filter(
        self, availabilities: list[CourtAvailability]
    ) -> list[CourtAvailability]:
        """
        Filter a set of availabilities based on duration.

        :param availabilities: The list of availabilities to filter.
        :type availabilities: list[CourtAvailability]
        :return: A list of availabilities which exceed a minimum duration.
        :rtype: list[CourtAvailability]
        """
        return [a for a in availabilities if a.duration >= self.min_duration]
