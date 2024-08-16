#!/bin/env python3
import os
import telebot

from datetime import date, timedelta

from goodminton.courts import UnknownLocationError, Summary, Location
from goodminton.filters import TimeRangeFilter, DurationFilter
from goodminton.scraper import scrape_bookings, invert_bookings

BOT_TOKEN = os.environ.get("BOT_TOKEN")

botminton = telebot.TeleBot(BOT_TOKEN)


@botminton.message_handler(commands=["hello"])
def send_welcome(message):
    botminton.reply_to(message, "🏸🏸🏸🏸🏸🏸")


@botminton.message_handler(commands=["poll"])
def create_poll(message):
    print(f"Recieved poll request: {message.text}")
    args = {}
    args.update([a.split("=") for a in message.text.split()[1:]])

    # Parse date range
    if "dates" not in args.keys():
        botminton.reply_to(
            message,
            "You need to supply a `dates` argument when using `/poll`, "
            + "e.g., `/poll dates=2024-08-16:2024-08-20`.",
        )
        return
    datestr_start, datestr_end = args["dates"].split(":")
    try:
        start = date.fromisoformat(datestr_start)
        dates = [start]
        end = date.fromisoformat(datestr_end)
        while start < end:
            start += timedelta(days=1)
            dates.append(start)
    except ValueError as e:
        botminton.reply_to(
            message, f"An error occurred when trying to parse `dates` argument: {e}"
        )
        return

    # Parse locations argument
    if "location" in args.keys():
        try:
            locations = [Location.from_str(args["location"])]
        except UnknownLocationError as e:
            botminton.reply_to(
                message,
                f"An error occurred when trying to parse `location` argument: {e}",
            )
            return
    else:
        locations = [Location.from_str("clayton"), Location.from_str("caulfield")]

    # Fetch availabilities
    avails = [
        avail
        for avails in [
            invert_bookings(scrape_bookings(loc, d.isoformat()))
            for loc in locations
            for d in dates
        ]
        for avail in avails
    ]

    # Parse timerange argument and filter
    if "timerange" in args.keys():
        avails = TimeRangeFilter.from_str(args["timerange"]).filter(avails)

    # Parse minduration argument and filter
    if "minduration" in args.keys():
        avails = DurationFilter.from_str(args["minduration"]).filter(avails)

    # Compute summaries
    summaries = Summary.compute_list(avails)

    # Send poll
    options = [telebot.types.PollOption(str(summary)) for summary in summaries]
    if len(options) > 1:
        botminton.send_poll(
            message.chat.id,
            "Which booking(s) are you available for?",
            options,
            allows_multiple_answers=True,
        )
    elif len(options) == 1:
        botminton.send_message(
            message.chat.id, f"There is only one option: {options[0]}"
        )
    else:
        botminton.send_message(
            message.chat.id, "There are no options which match your query."
        )


botminton.infinity_polling()
