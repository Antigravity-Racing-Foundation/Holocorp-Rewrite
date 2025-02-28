# This file generates the weekly event list for ZGR Weekly Time Trial.
from io_handler import ioScopes
from io_handler import ioRead

from enum import Enum, auto
import datetime 
import logging
import random
import time
import sys
import re

class GameChoice(Enum):
    HD = auto()
    HDZONE = auto()
    W2048 = auto()
    PULSE = auto()
    PULSEDLC = auto()

def generateRandomTrack(game: GameChoice) -> str:
    """
    Return a random race track from a game's pool.

    Args:
        game (GameChoice): Specifies the pool:
            - GameChoice.HD: Tracks available in normal race modes of WipEout HD;
            - GameChoice.HDZONE: Tracks available in Zone-based modes of WipEout HD;
            - GameChoice.W2048: Tracks available in WipEout 2048;
            - GameChoice.PULSE: Tracks available in normal race modes of WipEout Pulse (Base game);
            - GameChoice.PULSEDLC: Tracks available in normal race modes of WipEout Pulse (Base game + DLC);
            - Note: "Unknown range" will be returned if the `game.name` value is unhandled.
        
    Returns: 
        str: A random track from the specified pool.
    """
    match game.name:
        case "HD" | "HDZONE":

            trackBank = [
                "Vineta K",         "Anulpha Pass",     "Moa Therma",       "Chenghou Project", 
                "Metropia",         "Sebenco Climb",    "Ubermall",         "Sol 2", 
                "Talon's Junction", "Modesto Heights",  "The Amphiseum",    "Tech De Ra"
            ]

            additionalTrackBank =   ["Mallavol", "Corridon 12", "Pro Tozo", "Syncopia"]
            variantBank =           ["Forward", "Reverse"]     # my OCD knows no bounds

            if game.name == "hd": randomTrack = random.choice(trackBank)
            else: randomTrack = random.choice(trackBank + additionalTrackBank)

            if randomTrack in additionalTrackBank: return randomTrack 
            else: return f"{randomTrack} {random.choice(variantBank)}"

        case "W2048":

            trackBank = [
                "Empire Climb",     "Altima",       "Rockway Stadium",  "Subway",
                "Sol",              "Unity Square", "Queens Mall",      "Downtown", 
                "Capital Reach",    "Metro Park"
            ]

            return random.choice(trackBank)

        case "PULSE" | "PULSEDLC":

            trackBank = [
                "Talon's Junction", "Moa Therma",       "Metropia",         "Arc Prime",
                "De Konstruct",     "Tech De Ra",       "The Amphiseum",    "Fort Gale",
                "Basilico",         "Platinum Rush",    "Vertica",          "Outpost 7"
            ]

            additionalTrackBank =   ["Edgewinter", "Vostok Reef", "Gemini Dam", "Orcus"]
            variantBank =           ["White", "Black"] # this is how everything is ordered ingame btw

            if game.name == "pulse": realTrackBank = trackBank
            else: realTrackBank = trackBank + additionalTrackBank

            return f"{random.choice(realTrackBank)} {random.choice(variantBank)}"

        case _:
            return "Unknown range"


def generateRandomClass(game: GameChoice) -> str:
    """
    Return a random speed class from a game's pool.

    Args:
        game (GameChoice): Specifies the pool:
            - GameChoice.HD, GameChoice.HDZONE, GameChoice.PULSE, GameChoice.PULSEDLC: Speed classes available in WipEout HD and WipEout Pulse.
            - GameChoice.W2048: Speed classes available in WipEout 2048.
            - Note: "Unknown range" will be returned if the `game.name` value is unhandled.

    Returns: 
        str: A random speed class from the specified pool.
    """
    match game.name:
        case "HD" | "HDZONE" | "PULSE" | "PULSEDLC":
            classBank = ["Venom", "Flash", "Rapier", "Phantom"]
        case "W2048":
            classBank = ["C Class", "B Class", "A Class", "A+ Class"]
        case _:
            return "Unknown range"

    return random.choice(classBank)


def generateRandomShip(game: GameChoice) -> str:
    """
    Return a random ship from a game's pool.

    Args:
        game (GameChoice): Specifies the pool:
            - GameChoice.HD: Ships available in WipEout HD.
            - GameChoice.W2048: Ships available in WipEout 2048.
            - Note: "Unknown range" will be returned if the `game.name` value is unhandled.

    Returns: 
        str: A random ship from the specified pool.
    """
    match game.name:
        case "HD":
            teamBank = [
                "Feisar",               "Qirex",        "Piranha",              "AG-Systems",
                "Triakis Industries",   "Goteki 45",    "EG-X Technologies",    "Assegai Developments",
                "Mirage",               "Harimau",      "Auricom",              "Icaras"
            ]
            typeBank = ["[HD]", "[Fury]"]
        case "W2048":
            teamBank = ["Feisar",   "AG-Systems",   "Qirex",     "Auricom",      "Pir-hana"  ]
            typeBank = ["Speed",    "Agility",      "Fighter",   "Prototype"                 ]
        case _:
            return "Unknown range"

    return f"{random.choice(teamBank)} {random.choice(typeBank)}"


def getDeadlineTimestamp(week_num: int, year: int) -> int:
    """
    Return the timestamp of a week's end (Sunday, 11:59 PM).

    Args:
        week_num (int): The week's number in the year.
        year (int): The year.

    Returns:
        int: The week's end (Sunday, 11:59 PM).
    """
    firstDay = datetime.date(year, 1, 1)
    firstSunday = firstDay + datetime.timedelta(days=(6 - firstDay.weekday()) % 7)
    nextSunday = firstSunday + datetime.timedelta(weeks=week_num - 1)
    wantedTime = datetime.datetime.combine(nextSunday, datetime.time(23, 59))
    wantedTimeGmt = wantedTime.astimezone(datetime.timezone.utc)
    unixTimestamp = int(wantedTimeGmt.timestamp())
    return unixTimestamp


def generateEventList() -> str:
    """
    Return a set of ZGR Weekly Time Trial events based on the template. 
    See README.md -> Configuration -> `message_templates` -> `event_gen_template.md` for more information.

    Args:
        None.

    Returns:
        str: A set of ZGR Weekly Time Trial events.
    """
    currentDateTime = datetime.date.today()
    year, week_num, day_of_week = currentDateTime.isocalendar()

    pingId = ioRead(ioScopes.config, "zgrRolePing")
    template = ioRead(ioScopes.md, "event_gen_template.md")

    template = template.replace("!PING", pingId)\
    .replace("!YEAR", str(year))\
    .replace("!WEEK", str(week_num))\
    .replace("!DEADLINE", f"<t:{getDeadlineTimestamp(week_num, year)}:R>")

    timeoutCounter = 0
    while re.search("![A-Z0-9]+", template):
        template = template.replace("!TRACK2048", generateRandomTrack(GameChoice.W2048), 1)\
        .replace("!CLASS2048", generateRandomClass(GameChoice.W2048), 1)\
        .replace("!SHIP2048", generateRandomShip(GameChoice.W2048), 1)\
        .replace("!TRACKHD", generateRandomTrack(GameChoice.HD), 1)\
        .replace("!CLASSHD", generateRandomClass(GameChoice.HD), 1)\
        .replace("!SHIPHD", generateRandomShip(GameChoice.HD), 1)\
        .replace("!ZONEHD", generateRandomTrack(GameChoice.HDZONE), 1)
        timeoutCounter += 1
        if timeoutCounter > 24:
            logging.warning("[generateEventList] Exceeded maximum attempt counter, aborting...")
            break
        else:
            time.sleep(0.1)

    return template