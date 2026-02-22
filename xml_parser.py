# Handles all of the XML parsing, but also assembly into the final text block to be used in status.

from states import volatileStateSet
from states import firmStateSet

from io_handler import ioScopes
from io_handler import ioRead

from lookup_tables import *

from collections import defaultdict
import xml.etree.ElementTree as ET
from datetime import datetime
from inspect import signature
from functools import wraps
import requests
import hashlib
import logging
import re

volatileStates = volatileStateSet()
firmStates = firmStateSet()

#   Architecture:
#   XML parser -> various functions to convert raw values to usable ones -> output list
#   XML parser output list -> assembler -> lobby block based on .md templates

class UnknownXMLType(Exception):
    def __init__(self, message):
        super().__init__(message)

class ValuesClass():
    "This class is used by the parser as a namespace with the ability to merge a dictionary."
    def merge_dictionary(self, dict):
        self.__dict__.update(dict)

def enforceTypes(func):
    """Function decorator for argument type enforcing."""
    sig = signature(func)
    @wraps(func)
    def wrapper(*args, **kwargs):
        bound_args = sig.bind(*args, **kwargs)
        bound_args.apply_defaults()

        for name, value in bound_args.arguments.items():
            if name in func.__annotations__:
                target_type = func.__annotations__[name]
                try:
                    bound_args.arguments[name] = target_type(value)
                except Exception as e:
                    raise TypeError(f"Cannot convert argument '{name}' to {target_type}: {e}")

        return func(*bound_args.args, **bound_args.kwargs)
    return wrapper


# ---vvv--- Primary functions ---vvv---


def xmlToValues(resource: str) -> tuple[dict, bool]:
    """
    Parse an XML and return a dictionary with its values.

    Args:
        resource (str): The location of the XML that needs to be parsed. Must be either an HTTP(S) URL or a valid file path.

    Returns:
        dict:
            - The values fetched from the XML as a multi-dimensional array (see the Marshalling code blocks for structure reference);
            - None when no parsing was done due to hash being the same (see Bool below).
        bool: Whether or not the passed XML's hash was the same as the XML type's stored hash.

    Raises:
        FileNotFoundError: If a file path was passed as the `resource` argument, but the specified file does not exist.
        xml.etree.ElementTree.ParseError: If parsing of the fetched XML failed.
        xml_parser.UnknownXMLType: If the XML was parsed correctly, but the root's tag name (XML type) is unhandled.
    """

    if resource.startswith("http"):
        xmlData = requests.get(resource).content
    else:
        try:
            xmlData = open(resource).read().encode()
        except FileNotFoundError as e:
            logging.error("[xmlToValues] Non-URL resource passed, but file doesn't exist at that path!")
            raise e

    try:
        root = ET.fromstring(xmlData)
    except ET.ParseError as e:
        volatileStates.hashAPILobby = None
        volatileStates.hashAPIPlayers = None
        logging.warning("[xmlToValues] Unable to parse XML")
        raise e

    xmlHash = hashlib.sha1(xmlData).hexdigest()

    isSameFlag = False
    returnContents = None

    match root.tag:

        case "GetLobbyListing":
            if xmlHash == volatileStates.hashAPILobby:
                isSameFlag = True
            else:
                volatileStates.hashAPILobby = xmlHash

            if not isSameFlag:
                returnContents = []
                for lobby in root.findall("Lobby"):

                    # Small breakdown of these blocks' logic:
                    #
                    # Initial assignment takes everything and puts it into a dictionary, later merging it into a class for use as a namespace:
                    #   As a product of initial assignment, all variables that were in the XML can be expected to now be accessible in the `values` scope;
                    #
                    # Additional conversion does as the name implies:
                    #   Each name assigned at this stage should be used over the one it supersedes;
                    #
                    # Marshalling:
                    #   Can be used as a reference of the function's output.


                    # WipEout HD
                    if lobby.attrib["AppId"] == "23360":


                        # ---vvv--- Initial assignment ---vvv---


                        values = ValuesClass()
                        valuesDict = {}

                        for name, value in lobby.attrib.items():
                            valuesDict[name] = value

                        for stats in lobby.findall('GameStats'):
                            for variable in stats:
                                if variable.tag not in ["lobbyConfigPrimary", "lobbyConfigSecondary", "WeaponsConfigPrimary", "WeaponsConfigSecondary", "TrackList"]:
                                    valuesDict[variable.tag] = variable.text

                            for miscConfig in stats.find("LobbyConfigSecondary"):
                                valuesDict[miscConfig.tag] = True if miscConfig.text == "1" else False

                            for weapon in stats.find("WeaponsConfigPrimary"):
                                valuesDict[weapon.tag] = True if weapon.text == "1" else False

                            for weapon in stats.find("WeaponsConfigSecondary"):
                                valuesDict[weapon.tag] = True if weapon.text == "1" else False

                            values.tournamentTrackListIDs = []
                            for track in stats.find("TrackList"):
                                if track.text != "0": values.tournamentTrackListIDs.append(track.text)

                        values.merge_dictionary(valuesDict)


                        # ---vvv--- Additional conversion ---vvv---


                        values.dtObject = datetime.fromisoformat(values.GameCreateDt.replace("Z", "+00:00"))
                        values.UnixTimestamp = int(values.dtObject.timestamp())
                        values.PlayerLisParsed = marshalPlayerList(values.PlayerListCurrent)
                        values.TrackName = convertGameLevelToName(values.GameLevel)
                        values.GameMode = convertRulesetToMode(values.RuleSet)
                        values.SpeedClass, values.ClassLapCount = convertPlayerSkillToClass(values.PlayerSkillLevel)
                        values.WeaponsEnabled = True if values.GenericField1 == "1" else False

                        values.trackNameList = []
                        for track in values.tournamentTrackListIDs:
                            values.trackNameList.append(convertGameLevelToName(track))

                        if values.GameMode == "Eliminator":
                            values.Autopilot = None
                            values.Turbo = None
                            values.Shield = None


                        # ---vvv--- Marshalling ---vvv---


                        returnContents.append({
                            "AppId":            values.AppId,           "HostName":         values.HostName,            "Track":            values.TrackName,
                            "GameMode":         values.GameMode,        "SpeedClass":       values.SpeedClass,          "ClassLapCount":    values.ClassLapCount,
                            "LapCount":         values.LapCount,        "WeaponsEnabled":   values.WeaponsEnabled,      "PlayerCount":      values.PlayerCount,
                            "CreateDate":       values.UnixTimestamp,   "ElimTarget":       values.ElimTarget,          "ZBTarget":         values.ZBTarget,
                            "RaceProgress":     values.RaceProgress,    "PlayerList":       values.PlayerLisParsed,     "GameName":         values.GameName,

                            "AdditionalSettings": {
                                "PilotAssistAllowed":   values.PilotAssistAllowed,
                                "WeaponHints":          values.WeaponHints,
                                "BRsAllowed":           values.BRsAllowed,
                            },

                            "Weapons": {
                                "Rockets":  values.Rockets,    "Missiles": values.Missiles,   "Quake":        values.Quake,      "Turbo":    values.Turbo,
                                "Shield":   values.Shield,     "Cannon":   values.Cannon,     "Autopilot":    values.Autopilot,  "Plasma":   values.Plasma,
                                "Bomb":     values.Bomb,       "Mines":    values.Mines,      "LeechBeam":    values.LeechBeam
                            },

                            "TrackList": values.trackNameList
                        })


                        # --------- Done ---------


                    # WipEout Pulse
                    elif lobby.attrib["AppId"] == ("20794" or "21614" or "21634"):


                        # ---vvv--- Initial assignment ---vvv---


                        values = ValuesClass()
                        valuesDict = {}

                        for name, value in lobby.attrib.items():
                            valuesDict[name] = value

                        for stats in lobby.findall('GameStats'):
                            for variable in stats:
                                if variable.tag not in ["lobbyConfigPrimary", "lobbyConfigSecondary", "WeaponsConfigPrimary", "WeaponsConfigSecondary", "TrackList"]:
                                    valuesDict[variable.tag] = variable.text

                            values.tournamentTrackListIDs = []
                            for track in stats.find("TrackList"):
                                if track.text != "0": values.tournamentTrackListIDs.append(track.text)

                        values.merge_dictionary(valuesDict)


                        # ---vvv--- Additional conversion ---vvv---


                        values.dtObject = datetime.fromisoformat(values.GameCreateDt.replace("Z", "+00:00"))
                        values.UnixTimestamp = int(values.dtObject.timestamp())

                        values.PlayerLisParsed = marshalPlayerList(values.PlayerListCurrent)
                        values.TrackName = convertPulseGameLevelToName(values.GameLevel)
                        values.GameMode = convertPulseRulesetToMode(values.RuleSet)
                        values.SpeedClass, values.ClassLapCount = convertPlayerSkillToClass(values.PlayerSkillLevel)

                        values.WeaponsEnabled = True if values.Weapons == "1" else False
                        values.RaceInProgressFlag = True if values.RaceInProgress == "1" else False

                        values.trackNameList = []
                        for track in values.tournamentTrackListIDs:
                            values.trackNameList.append(convertPulseGameLevelToName(track))


                        # ---vvv--- Marshalling ---vvv---


                        returnContents.append({
                            "AppId":                values.AppId,              "GameName":         values.GameName,       "Track":            values.TrackName,
                            "GameMode":             values.GameMode,           "SpeedClass":       values.SpeedClass,     "CreateDate":       values.UnixTimestamp,
                            "MaxPlayers":           values.MaxPlayers,         "PlayerCount":      values.PlayerCount,    "WeaponsEnabled":   values.WeaponsEnabled,
                            "RaceInProgress":       values.RaceInProgressFlag, "TrackList":        values.trackNameList,  "PlayerList":       values.PlayerLisParsed
                        })


                        # --------- Done ---------

        case "GetPlayerCount":
            if xmlHash == volatileStates.hashAPIPlayers:
                isSameFlag = True
            else:
                volatileStates.hashAPIPlayers = xmlHash

            if not isSameFlag:
                returnContents = []
                for player in root.findall("Player"):
                    returnContents.append({"AppId": player.attrib["AppId"], \
                    "AccountName": player.attrib["AccountName"], \
                    "GameName": player.attrib["GameName"]})

        case _:
            raise UnknownXMLType(f"XML type {root.tag} is unhandled")

    return returnContents, isSameFlag




def lobbyListingAssembler(lobbyData: tuple) -> dict:
    """
    Produce a ready-to-use block of text containing lobby information based on the inputted list of values and templates.

    Args:
        lobbyData (tuple): List containing the lobby data and an `isSameFlag` boolean. Output of the `xmlToValues` function is expected.

    Returns:
        dict:
            - Text blocks containing lobby information, keyed by the AppId (the game);
            - None (if `isSameFlag` is True, meaning that the listing doesn't need to be updated);
            - An empty dict (if there are no lobbies).
    """

    # set all tourney progress instances to isStale = True to pop the stale ones later
    # (isStale is reset for a lobby if tourney progress calculation is invoked)
    for lobby in volatileStates.tourneyProgressByLobby:
        volatileStates.tourneyProgressByLobby[lobby][3] = True

    lobbies, isSameFlag = lobbyData

    if isSameFlag:
        return None # nothing to do case

    if not lobbies:
        return {} # empty listing case

    returnContents = defaultdict(list)

    for lobby in lobbies:
        tournamentProgression = False
        match lobby["AppId"]:

            # ---vvv--- Preset matching ---vvv---

            case "23360": # WipEout HD
                playerListTemplatePath = "lobby_formats/player_entry_hd.md"
                weaponIndication = formatWeaponsList(lobby["Weapons"], lobby["GameMode"])

                raceProgress = ""

                if firmStates.showVitaWarning and any(entry.get("Platform") == "Vita" for entry in lobby["PlayerList"]):
                    includeProgressVitaWarning = True
                else:
                    includeProgressVitaWarning = False

                match lobby["GameMode"]:
                    case "Single Race": # Один заезд
                        templatePath = "lobby_formats/block_templates/hd_single_race.md"
                        raceTarget = lobby["LapCount"]

                    case "Eliminator": # Охота
                        templatePath = "lobby_formats/block_templates/hd_eliminator.md"
                        raceTarget = lobby["ElimTarget"]
                        # TODO make it report elim progress (multiples of 100)

                    case "Zone Battle": # Битва за территорию
                        templatePath = "lobby_formats/block_templates/hd_zone_battle.md"
                        raceTarget = lobby["ZBTarget"]

                    case "Tournament": # Чемпионат
                        templatePath = "lobby_formats/block_templates/hd_tournament.md"
                        tournamentProgression = True

            case "20794": # WipEout Pulse
                playerListTemplatePath = "lobby_formats/player_entry_pulse.md"
                weaponIndication = f"{firmStates.assemblerElements["separator"]} Weapons off" if lobby["WeaponsEnabled"] else ""

                raceProgress = firmStates.assemblerElements["inprogress_pulse"] if lobby["RaceInProgress"] else ""

                match lobby["GameMode"]:
                    case "Single Race":
                        templatePath = "lobby_formats/block_templates/pulse_single_race.md"

                    case "Tournament":
                        templatePath = "lobby_formats/block_templates/pulse_tournament.md"

            case _:
                continue

        # ---vvv--- Assembly logic ---vvv---

        # Load templates
        template = ioRead(ioScopes.md, templatePath)
        playerListTemplate = ioRead(ioScopes.md, playerListTemplatePath)

        # Replace raw value keys
        matches = re.findall(r"!(\w+)", template)
        for key in matches:
            template = template.replace(f"!{key}", str(lobby[key]))

        # Replace player list processed key
        playerList = formatPlayerList(lobby["PlayerList"], playerListTemplate)
        template = template.replace("@PlayerList", playerList)

        # Replace additional settings processed key
        additionalSettings = ""
        try:
            if lobby["GameMode"] == "Zone Battle":
                # simple BR rule check specifically for ZB
                if not lobby["AdditionalSettings"]["BRsAllowed"]:
                    additionalSettings += f"{firmStates.assemblerElements["separator"]} BRs Off "
            else:
                for key in lobby["AdditionalSettings"]:
                    # catch additional settings that are disabled
                    if not lobby["AdditionalSettings"][key]:
                        lobbyProperty = key\
                        .replace("PilotAssistAllowed", "PA Off")\
                        .replace("WeaponHints", "Hints Off")\
                        .replace("BRsAllowed", "BRs Off") # pretty stiff but it works
                        additionalSettings += f"{firmStates.assemblerElements["separator"]} {lobbyProperty} "

        except KeyError as e:
            logging.debug(f"[lobbyListingAssembler] Key not in lobby properties array, game is probably Pulse... `{e}`")

        template = template.replace("@AdditionalSettings", additionalSettings)

        # Replace tourney race count processed key
        if tournamentProgression:
            template = template.replace("@RaceCount", str(len(lobby["TrackList"])))

        # Replace progress processed key
        if not raceProgress and not tournamentProgression:
            # pulse sets ^ this earlier, so we check it to know if we're dealing with HD
            raceProgress = calculateGameProgress(lobby["RaceProgress"], raceTarget, includeProgressVitaWarning)

        elif tournamentProgression:
            # tourney shit here
            # we call the tourney progress function, take the current race value and call the tourney list conversion function with it
            raceProgress, currentRaceNumber = \
            calculateTourneyProgress(lobby["RaceProgress"], lobby["LapCount"], len(lobby["TrackList"]), lobby["GameName"], includeProgressVitaWarning)

            trackList = calculateTourneyTrackList(lobby["TrackList"], currentRaceNumber)
            template = template.replace("@TrackList", trackList)

        template = template.replace("@Progress", raceProgress)

        # Replace weapon list processed key
        template = template.replace("@Weapons", weaponIndication)

        # Finish, add to output
        returnContents[lobby["AppId"]].append(template.strip())

    # TODO remove lap count from lobbies with the default
    # (make it an option, call this space "post-processing")

    # remove every tourney progress entry that isStale
    for lobby in list(volatileStates.tourneyProgressByLobby):
        if volatileStates.tourneyProgressByLobby[lobby][3] == True:
            del volatileStates.tourneyProgressByLobby[lobby]

    return returnContents




def playerListingAssembler(listingData: tuple) -> tuple[str, int]:
    """
    Produce a ready-to-use block of text containing player listing information based on the inputted list of values and templates.
    Lists players that aren't in a lobby. A counter of in-lobby players is appended at the end of the `str` output, if applicable.

    Args:
        listingData (tuple): List containing the player data and an `isSameFlag` boolean. Output of the `xmlToValues` function is expected.

    Returns:
        str:
            - A text block containing the player listing information;
            - None (if `isSameFlag` is True, meaning that the listing doesn't need to be updated);
            - An empty string (if there are no players or every player is in a lobby).

        int: The full player count.
    """

    players, isSameFlag = listingData

    # special case handling

    if isSameFlag == True:
        return None, None

    playerCount = len(players)

    if playerCount == 0:
        return {}, 0

    # done with that, now let's parse the list

    returnValue = ""

    playersHD = ""
    playersPulse = ""
    countHD = 0
    countPulse = 0

    for entry in players:

        if entry["GameName"]:
            playerName = ""
        else:
            playerName = entry["AccountName"]

        match entry["AppId"]:
            case "23360":
                if playerName: playersHD += f"{playerName}, "
                countHD += 1
            case "20794" | "21614" | "21634":
                if playerName: playersPulse += f"{playerName}, "
                countPulse += 1
            case _:
                pass

    playersListHD = marshalPlayerList(playersHD[:-2]) if playersHD else ""
    playersListPulse = marshalPlayerList(playersPulse[:-2]) if playersPulse else ""



    return "a", 2


    # returnContents = ""
    # listedPlayers = 0

    # for player in players:
    #     if not player["GameName"]:
    #         playerName = player["AccountName"].split("+")[0]\
    #         .replace("(PPSSPP)", "").strip() # this is a rather stiff way of doing this
    #         returnContents += f"{playerName}, "
    #         listedPlayers += 1

    # if listedPlayers == playerCount:
    #     returnContents = f"`{returnContents[:-2]}`"
    # else:
    #     returnContents = f"`{returnContents[:-2]}` and {playerCount - listedPlayers} more..."

    # return returnContents, playerCount


# ---vvv--- Internal functions ---vvv---


def marshalPlayerList(playerList: str) -> list:
    """
    Takes a player list string and returns a two-dimensional list with each player's properties.

    Args:
        playerList (str): The player list string. Format returned by the Thallium+Beat REST API is expected.
            - Expected format (example): "ThatOneBonk+PS3 (ru), ChaCheeChoo+Vita, kencho+PS3 (de) (RPCS3), dRoastedCat, ldywhite (PPSSPP)"

    Returns:
        list: A list with dictionaries for each player, containing their properties.
            - Example: [{'Name': 'ThatOneBonk', 'Region': 'ru', 'Platform': 'PS3'}, {'Name': 'ChaCheeChoo', 'Region': None, 'Platform': 'Vita'}]
            - Note: if an emulator tag is present, it overrides the physical `platform`.
    """
    playerArray = playerList.split(", ")

    playersMarshalled = []

    for player in playerArray:
        region = None
        name = None
        platform = None

        # Region
        pattern = r"\((\w{2})\)"
        match = re.search(pattern, player)

        if match:
            region = match.group(1)
            player = re.sub(pattern, "", player).strip()

        # Platform (Hardware)
        pattern = r"\((\w+)\)"
        match = re.search(pattern, player)

        if match:
            platform = match.group(1)
            player = re.sub(pattern, "", player).strip()

        # Platform (Meta, overrides Hardware if present)
        pattern = r"\+(\w+)"
        match = re.search(pattern, player)

        if match:
            player = re.sub(pattern, "", player).strip()
            if not platform:
                platform = match.group(1)

        # Set default (PSP is the only platform not signified on API in any way)
        if not platform:
            platform = "PSP"

        # Finished (nothing other than name left in `player`)
        playersMarshalled.append({"Name": player.strip(), "Region": region, "Platform": platform})

    return playersMarshalled




def formatPlayerList(playerList: list, template: str) -> str:
    """
    Takes a marshalled player `list` and fills a template with the data.

    Args:
        playerList (list): The marshalled player list (presumably, the output of marshalPlayerList).
        templatePath (str): The template which is to be filled with data.

    Returns:
        str: A formatted player list based on the template passed.
    """

    returnValue = ""
    for player in playerList:
        returnValue += template + "\n"

        # Flag assignment logic
        showVitaRegion = ioRead(ioScopes.config, "showVitaRegion")

        if player["Region"] != None: # have region
            player["Flag"] = f":flag_{player["Region"]}:"

        elif player["Platform"] == "Vita": # no region on vita
            player["Flag"] = ioRead(ioScopes.config, "emojiVitaFlagID")

        else: # no region on other platform
            player["Flag"] = ioRead(ioScopes.config, "emojiDebugFlagID")

        for key in re.findall(r"!(\w+)", returnValue):
            returnValue = returnValue.replace(f"!{key}", str(player[key]))

    return returnValue[:-1] # slice to remove the extra newline




def formatWeaponsList(weaponArray: dict, gameMode: str):
    """
    Takes a dictionary with weapon names and their states and returns a formatted weapon list based on the game mode.

    Args:
        weaponArray (dict): A dictionary containing weapon names and their states. Expected to be the ["Weapons"] key of xmlToValue's HD lobby output.
        gameMode (str): The game mode.

    Returns:
        str: The formatted weapon list string.
    """

    for weapon in list(weaponArray): # accomodate eliminator
        if weaponArray[weapon] == None:
            del weaponArray[weapon]

    if sum(weaponArray.values()) == len(weaponArray):
        return firmStates.assemblerElements["loadout_standard"]

    returnValue = ""

    if sum(weaponArray.values()) > len(weaponArray)/2: # display disabled weapons
        displayIndicator = firmStates.assemblerElements["loadout_disabled"]
        unwantedState = True

    else: # display enabled weapons
        displayIndicator = firmStates.assemblerElements["loadout_enabled"]
        unwantedState = False

    for weapon in list(weaponArray):
        if weaponArray[weapon] == unwantedState:
            del weaponArray[weapon]

    for weapon in weaponArray:
        # the below re puts spaces between PascalCase words
        returnValue += f"{re.sub(r'(?<!^)(?=[A-Z])', ' ', weapon)}, "
    returnValue = f"{returnValue[:-2]} {displayIndicator}"

    return returnValue




@enforceTypes
def calculateGameProgress(progress: int, target: int, includeVitaWarning: bool) -> str:
    """
    Return an approptiate event progress string based on the inputs.

    Args:
        progress (int): The current progress of the race.
        target (int): The race target.
        includeVitaWarning (bool): Whether or not to use a string template specific to Vita-included lobbies.

    Returns:
        str: The race progress indicator.
    """

    wantedElement = "inprogress_hd"

    if progress == 0:
        return ""
    elif progress < target:
        wantedElement = "inprogress_hd"
    elif progress > target:
        wantedElement = "returning"

    if includeVitaWarning:
        wantedElement += "_warn"

    return firmStates.assemblerElements[wantedElement]




@enforceTypes
def calculateTourneyProgress(raceProgress: int, raceTarget: int, raceCount: int, lobbyName: str, includeVitaWarning: bool) -> tuple[str, int]:
    """
    Calculates the progress of a tourney based on cues and returns the appropriate progress indicator message.

    Args:
        raceProgress (int): The progress of the tournament's current race.
        raceTarget (int): The target (total lap count) of the tournament's current race.
        raceCount (int): The total number of races in the tournament.
        lobbyName (str): The lobby name (not host's player name!).
        includeVitaWarning (bool): Whether or not to include the PS Vita player warning.

    Returns:
        str: The progress indicator message.
        int: The number of the race in the list currently being played.
    """
    currentRaceNumber, raceNumberAlreadyUpdated, lastTourneyDone, isStale = \
    volatileStates.tourneyProgressByLobby.setdefault(lobbyName, [1, False, False, False])

    # the currentRaceNumber should only be reset when the tournament truly ends
    # (when lastTourney is Done and raceProgress is reset to 0 on returning to lobby)
    # that way, it will only report currentRaceNumber as 1 for the next tournament,
    # not the current one when it is still returning to the lobby
    if lastTourneyDone == True and raceProgress == 0:
        currentRaceNumber = 1
        lastTourneyDone = False

    if includeVitaWarning == True:
        wantedElement = "inprogress_hd_tourney_warn"
    else:
        wantedElement = "inprogress_hd_tourney"

    if raceProgress <= raceTarget:
        raceNumberAlreadyUpdated = False
    elif raceNumberAlreadyUpdated == False:
        currentRaceNumber += 1
        raceNumberAlreadyUpdated = True
        if currentRaceNumber > raceCount:
            lastTourneyDone = True # tourney end check
            currentRaceNumber -= 1 # this is kinda stupid but i like it :p

    volatileStates.tourneyProgressByLobby[lobbyName] = [currentRaceNumber, raceNumberAlreadyUpdated, lastTourneyDone, False]

    if raceProgress == 0 and currentRaceNumber == 1:
        return "", -1 # tourney prestart check

    return firmStates.assemblerElements[wantedElement], currentRaceNumber




def calculateTourneyTrackList(trackList: list, currentRaceNumber: int):
    """
    Converts a list of track names in a tournament into a formatted string.

    Args:
        trackList (list): The tournament track list.
        currentRaceNumber (int): The number of the race in the list currently being played.
    """
    functionOutput = "-# ‎   ["
    trackParserCounter = 0

    for track in trackList:
        if currentRaceNumber - 1 == trackParserCounter:
            functionOutput = f"{functionOutput} | **__{track}__**"
        else:
            functionOutput = f"{functionOutput} | {track}"
        trackParserCounter += 1

        if trackParserCounter % 4 == 0 and trackParserCounter != 0:
            functionOutput = f"{functionOutput}]\n-# ‎   ["

    functionOutput += "]"
    return functionOutput.replace("[ | ", "[")\
    .replace("[]", "") # hacky formatting stuff :p
