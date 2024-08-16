# Tools for scraping the public Monash sport website for bookings.
from bs4 import BeautifulSoup
from urllib.request import urlopen
from datetime import datetime, date, time

import tree_sitter_javascript as tsjs
from tree_sitter import Language, Parser

from goodminton.courts import CourtBooking, CourtAvailability, Location


URL_CAULFIELD = "https://www.mymonashsport.com.au/public/facility/iframe/753/1030/"
URL_CLAYTON = "https://www.mymonashsport.com.au/public/facility/iframe/754/1018/"

JS_LANG = Language(tsjs.language())

COURT_BOOKINGS_QUERY = JS_LANG.query(
    """
(
    (pair
        key: (property_identifier) @key-name
        value: (array) @array
    )
    (#eq? @key-name "events")
)
"""
)

DATES_QUERY = JS_LANG.query(
    """
(
    (new_expression
        constructor: (identifier) @name
        arguments: (arguments) @args
    )
    (#eq? @name "Date")
)
"""
)


def scrape_bookings(location: Location, date_iso: str):
    """
    Fetch all badminton bookings for the specified location and date.

    :param location: The monash sport location
    :type location: Location
    :param date_iso: A date string in ISO format "YYYY-MM-DD"
    :type date_iso: str
    :return: A dict with keys equal to the court names and values are
             lists of dicts with keys 'start' and 'end' and datetime values.
    :rtype: dict[str, list[dict[str, datetime]]]
    """
    # Construct URL to scrape
    if location == Location.CLAYTON:
        url = URL_CLAYTON + date_iso
    elif location == Location.CAULFIELD:
        url = URL_CAULFIELD + date_iso

    # Fetch the HTML
    out = urlopen(url).readlines()
    html = "".join([b.decode("UTF-8") for b in out])
    soup = BeautifulSoup(html, features="html.parser")

    # Parse the court names
    court_names = [
        td.text.strip() for td in soup.findAll(lambda tag: tag.name == "td")
    ][1:]
    court_id_to_names = {}
    court_id_to_names.update(enumerate(court_names))

    # Get the script which populates the table
    script = soup.findAll(lambda tag: tag.name == "script")[3].contents[0]

    # Parse the javascript
    parser = Parser(JS_LANG)
    tree = parser.parse(script.encode("UTF-8"))
    court_bookings_raw = [
        o[1]["array"] for o in COURT_BOOKINGS_QUERY.matches(tree.root_node)
    ]
    bookings = []
    for court_id, bookings_data in enumerate(court_bookings_raw):
        # Extract the booking times
        booking_times_raw = [
            booking[1]["args"] for booking in DATES_QUERY.matches(bookings_data)
        ]
        # Convert list of integers to datetimes
        booking_times = [
            datetime.combine(
                date.fromisoformat(date_iso),
                time(
                    *[
                        int(num.text.decode("UTF-8"))
                        for num in b.children
                        if num.type == "number"
                    ][3:]
                ),
            )
            for b in booking_times_raw
        ]
        # Construct CourtBooking objects
        while booking_times:
            end = booking_times.pop()
            start = booking_times.pop()
            bookings.append(
                CourtBooking(
                    location=location,
                    court_name=court_id_to_names[court_id],
                    start=start,
                    end=end,
                )
            )
    return bookings


def invert_bookings(bookings: list[CourtBooking]) -> list[CourtAvailability]:
    """
    Get available time slots given the bookings (from `scrape_bookings`).

    :param bookings: A list of court bookings.
    :type bookings: list[CourtBooking]
    :return: An "inverted" list of court availabilities corresponding to the
             spaces in-between the bookings.
    :rtype: list[CourtAvailability]
    """
    availabilities = []
    courts = set([b.court_name for b in bookings])
    # For each court, we extract the spaces between bookings.
    for court in courts:
        court_bookings = [b for b in bookings if b.court_name == court]
        # Sort by starting time. We assume here that they never overlap, which
        # should always hold.
        court_bookings.sort(key=lambda b: b.start)
        later = court_bookings.pop()
        while court_bookings:
            earlier = court_bookings.pop()
            availabilities.append(
                CourtAvailability(
                    start=earlier.end,
                    end=later.start,
                    court_name=court,
                    location=earlier.location,
                )
            )
            later = earlier
    return availabilities
