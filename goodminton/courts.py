# Data types for badminton court availabilities
from dataclasses import dataclass
from enum import Enum

from datetime import datetime, date, time


def format_date(d: date) -> str:
    "Format dates as 'dd Month'"
    return d.strftime("%d %B")


def format_time(t: time) -> str:
    "Format times as 'hh:mm am/pm'"
    return t.strftime("%I:%M %P")


def duration_hours(dt1: datetime, dt2: datetime) -> float:
    "Calculate duration in number of hours"
    td = abs(dt1 - dt2)
    return td.seconds / (60 * 60)


class UnknownLocationError(Exception):
    """
    An exception to be raised when location string does not match any known
    Monash sport location.
    """

    pass


class Location(Enum):

    "An enum for encoding Monash sport locations"

    CLAYTON = "Clayton"
    CAULFIELD = "Caulfield"

    @classmethod
    def from_str(cls, s):
        if s.lower() == cls.CLAYTON.value.lower():
            return cls.CLAYTON
        elif s.lower() == cls.CAULFIELD.value.lower():
            return cls.CAULFIELD
        else:
            raise UnknownLocationError(
                "Location not recognised. Expected one of 'clayton' or " "'caulfield'."
            )

    def __str__(self):
        return self.value


@dataclass
class CourtBooking:

    "A dataclass for encoding times when a court is unavailable"

    location: Location
    court_name: str
    start: datetime
    end: datetime

    @property
    def duration(self) -> float:
        return duration_hours(self.start, self.end)

    def __repr__(self):
        date = format_date(self.start.date())
        start_time = format_time(self.start)
        end_time = format_time(self.end)
        return (
            f"{self.location} ({self.court_name}) on {date} "
            f"for {self.duration:.2f} hours ({start_time} to {end_time})."
        )


@dataclass
class CourtAvailability:

    "A dataclass for encoding times when a court is available."

    location: Location
    court_name: str
    start: datetime
    end: datetime

    @property
    def duration(self) -> float:
        return duration_hours(self.start, self.end)

    def __repr__(self):
        date = format_date(self.start.date())
        start_time = format_time(self.start)
        end_time = format_time(self.end)
        return (
            f"{self.location} ({self.court_name}) on {date}"
            f"for {self.duration:.2f} hours ({start_time} to {end_time})."
        )


@dataclass
class Summary:

    "A dataclass for storing summaries of availabilities."

    location: Location
    date: date
    start: time
    num_courts: int
    max_duration: float
    min_duration: float

    @classmethod
    def compute_list(cls, availabilities: list[CourtAvailability]):
        summaries = []
        locs = set([a.location for a in availabilities])
        for loc in locs:
            loc_availabilities = [a for a in availabilities if a.location == loc]
            starts = set([a.start for a in loc_availabilities])
            for s in starts:
                s_loc_availabilities = [a for a in loc_availabilities if a.start == s]
                num_courts = len(s_loc_availabilities)
                max_duration = max([a.duration for a in s_loc_availabilities])
                min_duration = min([a.duration for a in s_loc_availabilities])
                summaries.append(
                    cls(
                        location=loc,
                        date=s.date(),
                        start=s.time(),
                        num_courts=num_courts,
                        max_duration=max_duration,
                        min_duration=min_duration,
                    )
                )
        return summaries

    def __repr__(self):
        d = format_date(self.date)
        t = format_time(self.start)
        return (
            f"{self.location} on {d} from {t} "
            f"({self.num_courts} courts, up to {self.max_duration} hours)"
        )
