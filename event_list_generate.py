# This file generates the weekly event list for ZGR Weekly Time Trial.
from io_handler import ioScopes
from io_handler import ioRead

import datetime 
import random
import sys

def generateRandomTrack(trackList):
    random.seed()
    trackBank = ["Vineta K", "Anulpha Pass", "Moa Therma", "Chenghou Project", 
    "Metropia", "Sebenco Climb", "Ubermall", "Sol 2", 
    "Talon's Junction", "Modesto Heights", "The Amphiseum", "Tech De Ra", # index 0-11, reversable
    "Mallavol", "Corridon 12", "Pro Tozo", "Syncopia", # index 12-15-25, not reversable
    "Empire Climb", "Altima", "Rockway Stadium", "Subway",
    "Sol", "Unity Square", "Queens Mall", "Downtown", 
    "Capital Reach", "Metro Park",
    "Talon's Junction", "Moa Therma", "Metropia", "Arc Prime", # index 26-41, blackfaceable
    "De Konstruct", "Tech De Ra", "The Amphiseum", "Fort Gale",     # i am aware that most of these are duplicated in
    "Basilico", "Platinum Rush", "Vertica", "Outpost 7",            # the HD bank but i don't wanna fuck with that man
    "Edgewinter", "Vostok Reef", "Gemini Dam", "Orcus"]
    match trackList:
        case "hd":
            if random.getrandbits(1) == 1:
                return trackBank[random.randint(0, 11)] + " Reverse"
            else:
                return trackBank[random.randint(0, 11)] + " Forward"

        case "hdZone":
            randomInt = random.randint(0, 15)
            if randomInt < 12:

                if random.getrandbits(1) == 1: # this looks messy but don't worry about it
                    return trackBank[randomInt] + " Reverse"
                else:
                    return trackBank[randomInt] + " Forward"

            else:
                return trackBank[randomInt]
        
        case "2048":
            return trackBank[random.randint(16, 25)] 
        
        case "pulse" | "pulseDLC":
            indexEnd = 37 if trackList == "pulse" else 41
            if random.getrandbits(1) == 1:
                return trackBank[random.randint(26, indexEnd)] + " Black"
            else:
                return trackBank[random.randint(26, indexEnd)] + " White"


def generateRandomClass(game):
    random.seed() # i'm not actually sure if this does anything but yknow being safe and it doesn't hurt
    classBank = ["Venom", "Flash", "Rapier", "Phantom", "C Class", "B Class", "A Class", "A+ Class"] # 0-3 hd 4-7 2048

    match game:
        case "hd":
            return classBank[random.randint(0, 3)]
        case "2048":
            return classBank[random.randint(4, 7)]


def generateRandomShip(game):
    random.seed()
    teamBank = ["Piranha", "Assegai Developments", "Harimau", "Mirage",
    "Triakis Industries", "Icaras", "Goteki 45", "EGX Technologies",
    "Feisar", "AG-Systems", "Qirex", "Auricom", "Pir-hana"] # 0-11 hd, 8-12 2048

    shipClassBank = [" Speed", " Agility", " Fighter", " Prototype"]

    match game:
        case "hd":
            if random.getrandbits(1) == 1:
                return teamBank[random.randint(0, 11)] + " [Fury]"
            else:
                return teamBank[random.randint(0, 11)] + " [HD]"
        case "2048":
            return teamBank[random.randint(8, 12)] + shipClassBank[random.randint(0, 3)]



def getDeadlineTimestamp(week_num, year):
    firstDay = datetime.date(year, 1, 1)
    firstSunday = firstDay + datetime.timedelta(days=(6 - firstDay.weekday()) % 7)
    nextSunday = firstSunday + datetime.timedelta(weeks=week_num - 1)
    wantedTime = datetime.datetime.combine(nextSunday, datetime.time(23, 59))
    wantedTimeGmt = wantedTime.astimezone(datetime.timezone.utc)
    unixTimestamp = int(wantedTimeGmt.timestamp())
    return unixTimestamp


def generateEventList():
    currentDateTime = datetime.date.today()
    year, week_num, day_of_week = currentDateTime.isocalendar()

    pingId = ioRead(ioScopes.config, "zgrRolePing")
    template = ioRead(ioScopes.md, "event_gen_template.md")

    return template.replace("!PING", pingId)\
    .replace("!YEAR", str(year))\
    .replace("!WEEK", str(week_num))\
    .replace("!TRACK2048", generateRandomTrack("2048"))\
    .replace("!CLASS2048", generateRandomClass("2048"))\
    .replace("!SHIP2048", generateRandomShip("2048"))\
    .replace("!TRACKOMEGA", generateRandomTrack("hd"))\
    .replace("!CLASSOMEGA", generateRandomClass("hd"))\
    .replace("!SHIPOMEGA", generateRandomShip("hd"))\
    .replace("!TRACKHD", generateRandomTrack("hd"))\
    .replace("!CLASSHD", generateRandomClass("hd"))\
    .replace("!SHIPHD", generateRandomShip("hd"))\
    .replace("!ZONEOMEGA", generateRandomTrack("hdZone"))\
    .replace("!ZONEHD", generateRandomTrack("hdZone"))\
    .replace("!DETOOMEGA", generateRandomTrack("hdZone"))\
    .replace("!DETOHD", generateRandomTrack("hdZone"))\
    .replace("!DEADLINE", f"<t:{getDeadlineTimestamp(week_num, year)}:R>")