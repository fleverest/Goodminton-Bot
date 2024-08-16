# Data types for badminton court availabilities
from dataclasses import dataclass
from enum import Enum

from datetime import datetime, date, time, timedelta


def format_date(d: date) -> str:
    "Format dates as 'dd Month'"
    return d.strftime("%d %B")


def format_time(t: time) -> str:
    "Format times as 'hh:mm am/pm'"
    return t.strftime("%I:%M %P")


def format_duration(dt1: datetime, dt2: datetime) -> str:
    "Format timedelta in number of hours (2 dec. places)"
    td = abs(dt1 - dt2)
    hours = td.seconds / (60 * 60)
    return f"{hours:.2f}"


class UnknownLocation(Exception):
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
        if s.lower() == cls.CLAYTON.lower():
            return cls.CLAYTON
        elif s.lower() == cls.CAULFIELD.lower():
            return cls.CAULFIELD
        else:
            raise UnknownLocation(
                "Location not recognised. Expected one of 'clayton' or "
                "'caulfield'."
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
    def duration(self) -> str:
        return format_duration(self.start, self.end)

    def __repr__(self):
        date = format_date(self.start.date())
        start_time = format_time(self.start)
        end_time = format_time(self.end)
        return (
            f"{self.location} ({self.court_name}) on {date}"
            f" from {start_time} to {end_time}"
        )


@dataclass
class CourtAvailability:

    "A dataclass for encoding times when a court is available."

    location: Location
    court_name: str
    start: datetime
    end: datetime

    @property
    def duration(self) -> str:
        return format_duration(self.start, self.end)

    def __repr__(self):
        date = format_date(self.start.date())
        start_time = format_time(self.start)
        end_time = format_time(self.end)
        return (
            f"{self.location} ({self.court_name}) on {date}"
            f" from {start_time} to {end_time}"
        )
