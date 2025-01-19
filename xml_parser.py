# This is the heart of the bot. The magic happens here.
import requests
import xml.etree.ElementTree as ET
import logging
import re
from datetime import datetime
from lookup_tables import *
from config_handler import *
import hashlib

global appId

# this dict will have lobby name as key, current race, last update and tourney finished flag
tourneyProgressByLobby = {}
tourneyProgressFunctionIsIdle = "False"

urlListing = configPull("apiLobbiesURL")
urlCount = configPull("apiPlayersURL")
showVitaWarning = configPull("showVitaWarning")
vitaFlag = configPull("emojiVitaFlagID")
debugFlag = configPull("emojiDebugFlagID")
showVitaRegion = configPull("showVitaRegion")

def parseWeaponArray(weaponArray, mode):
    logging.debug(f"[Weapon array parser] Start parsing weapon list for {mode}")

    match mode:
        case "Single Race":
            indexToList = weaponIndexesToList
            leastElementComparisonValue = 5 # this is the best name i could come up with for this variable
        case "Eliminator":
            indexToList = eliminatorWeaponIndexesToList
            leastElementComparisonValue = 1
            weaponArray.pop(6) # remove weapons disabled in eliminator
            weaponArray.pop(4)
            weaponArray.pop(3)
        case _:
            return "null"

    # first and foremost,
    if weaponArray.count("0") == 0:
        return "Default weapon loadout"

    weaponList = {}
    weaponIndexCounter = 0
    functionFinalOutput = ""

    for entry in weaponArray:
        weaponList[indexToList(weaponIndexCounter)] = entry # put every weapon and its status in the list based on index
        weaponIndexCounter += 1

    if weaponArray.count("1") > leastElementComparisonValue: # the count ensures that the least data is always used to represent the configuration
        for key, value in weaponList.items():
            if value == '0':
                functionFinalOutput = f"{functionFinalOutput}, {key}"
        return f"{functionFinalOutput} disabled".removeprefix(", ")

    else:
        for key, value in weaponList.items():
            if value == '1':
                functionFinalOutput = f"{functionFinalOutput}, {key}"
        return f"{functionFinalOutput} enabled".removeprefix(", ")

def calculateTourneyProgress(raceProgress, raceTarget, raceCount, lobbyName, includeVitaWarning):
    global tourneyProgressByLobby
    global tourneyProgressFunctionIsIdle
    raceProgress = int(raceProgress)
    raceTarget = int(raceTarget)
    raceCount = int(raceCount)
    vitaWarningPostfix = ""
    vitaWarningPrefix = ""
    
    tourneyProgressFunctionIsIdle = "False"

    currentRaceNumber, raceNumberAlreadyUpdated, lastTourneyDone = tourneyProgressByLobby.setdefault(lobbyName, (1, "False", "False"))

    if lastTourneyDone == "True" and raceProgress == 0: # reset stuff only on next tourney load becasue if we reset it immediately
        currentRaceNumber = 1                           # after the old one ends, it'll report progress as 1 until it returns to lobby
        lastTourneyDone = "False"

    if includeVitaWarning == "True":
        vitaWarningPrefix = ", HOLD ON!"
        vitaWarningPostfix = "\n-# ‎   Due to a bug, Vita players will be kicked if someone joins mid-race. Please wait for the race to finish."

    if raceProgress <= raceTarget:
        raceNumberAlreadyUpdated = "False"
    elif raceNumberAlreadyUpdated == "False":
        currentRaceNumber += 1
        raceNumberAlreadyUpdated = "True"
        if currentRaceNumber > raceCount:
            lastTourneyDone = "True" # tourney end check
            currentRaceNumber -= 1 # this is kinda retarded but i like it :p
    
    tourneyProgressByLobby[lobbyName] = (currentRaceNumber, raceNumberAlreadyUpdated, lastTourneyDone)

    if raceProgress == 0 and currentRaceNumber == 1:
        return "", -1 # tourney prestart check

    return f"\n**   >> TOURNEY IN PROGRESS{vitaWarningPrefix} <<**{vitaWarningPostfix}", currentRaceNumber

def calculateGameProgress(progress, target, includeVitaWarning):
    progress = int(progress)
    target = int(target)
    vitaWarningPostfix = ""
    vitaWarningPrefix = ""
    if includeVitaWarning == "True":
        vitaWarningPrefix = ", HOLD ON!"
        vitaWarningPostfix = "\n-# ‎   Due to a bug, Vita players will be kicked if someone joins mid-race. Please wait for the race to finish."

    if progress <= target and progress != 0:
        return f"\n**   >> RACE IN PROGRESS{vitaWarningPrefix} <<**{vitaWarningPostfix}"
    elif progress > target:
        return f"\n**   >> RETURNING TO LOBBY{vitaWarningPrefix} <<**{vitaWarningPostfix}"
    else:
        return ""

def convertTourneyTrackList(trackList, game, currentRaceNumber = -1):   # this function has a lot of formatting stuff going on
    match game:                                 # if you see some random characters that you don't know the purpose of, don't think about it
        case "HD":
            IDToName = convertGameLevelToName
        case "Pulse":
            IDToName = convertPulseGameLevelToName

    functionFinalOutput = "["
    trackParserCounter = 0

    for track in trackList:
        if currentRaceNumber - 1 == trackParserCounter:
            functionFinalOutput = f"{functionFinalOutput} | **__{IDToName(track)}__**"
        else:
            functionFinalOutput = f"{functionFinalOutput} | {IDToName(track)}"
        trackParserCounter += 1

        if trackParserCounter == 4:
            functionFinalOutput = f"{functionFinalOutput}]\n-# ‎   ["
            trackParserCounter = 0
        
    functionFinalOutput = f"{functionFinalOutput}]"
    return functionFinalOutput.replace("[ | ", "[")\
    .replace("[]", "") # hacky formatting stuff :p

def convertPlayerList(playerList, game):
    platformLabelPSP = configPull("platformLabelPSP")
    platformLabelPPSSPP = configPull("platformLabelPPSSPP")
    platformLabelPS3 = configPull("platformLabelPS3")
    platformLabelVita = configPull("platformLabelVita")
    platformLabelRPCS3 = configPull("platformLabelRPCS3")
    global vitaFlag
    global debugFlag

    if game == "pulse" and configPull("pulseShowRegions") == "False": # choo wanted (PSP) regardless of bot config so this was born
        playerList = f"{playerList},"\
        .replace(",", f" {platformLabelPSP},")\
        .rstrip(",")\
        .replace(f"(PPSSPP) {platformLabelPSP}", f"{platformLabelPPSSPP}") # pretty smart eh?
        playerListPrefix = configPull("pulsePlayerListPrefix")
        return "\n" + playerListPrefix + playerList.replace(', ', f'\n{playerListPrefix}')

    class playerEntry: # this implementation of player list digestion was ported over from Legacy becuase it's p much perfect
        def __init__(self, name):
            self.name = name
            self.region = None
            self.platform = None
        def add_info(self, region, platform):
            self.region = region
            self.platform = platform
        def update_name(self, new_name):
            self.name = new_name
        def __repr__(self):
            return f"{self.region} {self.name} {self.platform}"

    playerList = str(playerList).split(", ")
    playerEntryArray = [playerEntry(name) for name in playerList]
    playerListPrintable = ""

    for entry in playerEntryArray:
        entryPlatform = platformLabelPSP # the only reason why this wouldn't be changed later would be because you're on PSP
        if "+PS3" in entry.name:
            entryPlatform = platformLabelPS3
            entry.update_name(entry.name.replace("+PS3", ""))
        if "+Vita" in entry.name:
            entryPlatform = platformLabelVita
            entry.update_name(entry.name.replace("+Vita", ""))
        if "(RPCS3)" in entry.name:
            entryPlatform = platformLabelRPCS3
            entry.update_name(entry.name.replace("+PS3", ""))
            entry.update_name(entry.name.replace(" (RPCS3)", ""))
        if "(PPSSPP)" in entry.name:
            entryPlatform = platformLabelPPSSPP
            entry.update_name(entry.name.replace(" (PPSSPP)", ""))

        pattern = r'\((\w{2})\)'
        match = re.search(pattern, entry.name)

        if match:
            entryRegion = f":flag_{match.group(1)}:"
            entry.update_name(re.sub(pattern, '', entry.name).strip())
        else:
            entryRegion = debugFlag

        if "Vita" in entryPlatform and showVitaRegion == "False":
            entryRegion = vitaFlag

        entry.add_info(entryRegion, entryPlatform)
        playerListPrintable = playerListPrintable + f"\n   {entry}"

    return playerListPrintable

def fetchLobbyList():
    global tourneyProgressFunctionIsIdle 

    xmlData = requests.get(urlListing) # variable initialization
    try:
        with open("../GetLobbyListing.xml", "r") as exampleXMLFile:
            xmlOfflineData = exampleXMLFile.read()
    except:
        logging.debug("[fetchLobbyList] Couldn't open the example XML, to be expected on production")
    parsingResultsHD = ""
    parsingResultsPulse = ""
    raceProgress = ""
    
    try:
        #root = ET.fromstring(xmlOfflineData)
        root = ET.fromstring(xmlData.content)
    except ET.ParseError:
        logging.warning("[Lobby XML Parser] Bad XML passed")
        return "failureApiFault"

    xmlHash = hashlib.sha1(xmlData.content).hexdigest() # calculate hash to not do same work more than once
    if xmlHash == workspacePull("lobbies"):
        return "nothingToDo"
    else: 
        workspaceStore(xmlHash, "lobbies")

    if root.findall('Lobby') == []: # terminate task if no lobbies are in the list (arrays will crash the program otherwise)
        logging.debug("[Lobby XML Parser] XML passed is empty")
        return "No lobbies are up."

    # tournament progression listing bugfix
    # okay basically listing breaks if the tournament ends prematurely because the function can't account for that so the variables aren't reset
    # so the next tournament race counter is off by some number and you can't fix it and it'll stay like that forever
    # which is why we watch to make sure that if the tournament function isn't invoked, the dict is nuked, so that leftover variables (if any) aren't
    # passed down
    # this could be done per-lobby as well but that would be way more complicated than this single bool and i honestly cannot be arsed to do that
    # for the specific case of someone holding two tournaments then one of them ending prematurely then that person restarting the tournament and wondering
    # why it's broken

    tourneyProgressFunctionIsIdle = "True"

    for lobby in root.findall('Lobby'): # let's get xml'ing!!!! this loop will parse each lobby, put its properties into variables and compose it into a text block
        appId = lobby.attrib["AppId"] # the appId determines what game the parsing will be done for
            
        match appId:
            case "23360": # this appId is for WipEout HD


                # ---###--- WIPEOUT HD PARSING START ---###---


                propertyTournamentTrackListIDs = []
                propertyWeaponList = []

                propertyGameName = lobby.attrib["GameName"]
                propertyTrack = convertGameLevelToName(lobby.attrib["GameLevel"])
                propertyGameMode = convertRulesetToMode(lobby.attrib["RuleSet"])
                propertySpeedClass, propertyDefaultLapCount = convertPlayerSkillToClass(lobby.attrib["PlayerSkillLevel"])
                propertyPlayerList = lobby.attrib["PlayerListCurrent"]
                propertyWeaponsEnabled = lobby.attrib["GenericField1"]
                propertyPlayerCount = lobby.attrib["PlayerCount"]
                propertyCreateDate = lobby.attrib["GameCreateDt"]
                propertyMiscSettings = ""

                dtObject = datetime.fromisoformat(propertyCreateDate.replace("Z", "+00:00"))
                propertyCreateDate = int(dtObject.timestamp())

                for stats in lobby.findall('GameStats'):
                    for config in stats:
                        if config.tag == "HostName": propertyLobbyName = config.text 
                        if config.tag == "LapCount": propertyLapCount = config.text 
                        if config.tag == "ElimTarget": propertyElimTarget = config.text 
                        if config.tag == "ZBTarget": propertyZBTarget = config.text 
                        if config.tag == "RaceProgress": propertyRaceProgress = config.text 

                    for miscStats in stats.findall("LobbyConfigSecondary"):
                        for miscConfig in miscStats:
                            if miscConfig.tag == "WeaponHints" and miscConfig.text == "0" and propertyWeaponsEnabled == "1": propertyMiscSettings = f"{propertyMiscSettings} // Hints Off"
                            if miscConfig.tag == "BRsAllowed" and miscConfig.text == "0": propertyMiscSettings = f"{propertyMiscSettings} // BRs Off" 
                            if miscConfig.tag == "PilotAssistAllowed" and miscConfig.text == "0" and propertyGameMode != "Zone Battle": propertyMiscSettings = f"{propertyMiscSettings} // PA Off"
                    
                    for weaponsPrimary in stats.findall("WeaponsConfigPrimary"):
                        for weapon in weaponsPrimary:
                            propertyWeaponList.append(weapon.text)

                    for weaponsSecondary in stats.findall("WeaponsConfigSecondary"):
                        for weapon in weaponsSecondary:
                            propertyWeaponList.append(weapon.text)

                    for trackList in stats.findall("TrackList"):
                        for track in trackList:
                            propertyTournamentTrackListIDs.append(track.text)
                            propertyTourneyTrackCount = trackList.attrib["totalEntries"]

                # this approach to paring the xml may not be the most optimal but it's much more readable than what we had before and
                # it's also good enough performance-wise

                playerListPrintable = convertPlayerList(propertyPlayerList, "hd")

                if propertyDefaultLapCount == propertyLapCount:
                    listingLapCount = ""
                else:
                    listingLapCount = f" ({propertyLapCount} Laps)"


                # ---###--- ASSEMBLE HD LOBBY BLOCK ---###---


                match propertyGameMode:
                    case "Single Race":
                        weaponAddendum = parseWeaponArray(propertyWeaponList, "Single Race") if propertyWeaponsEnabled == "1" else "Weapons disabled"
                        includeVitaWarning = "True" if showVitaWarning == "True" and "+Vita" in propertyPlayerList else "False"
                        progressAddendum = calculateGameProgress(propertyRaceProgress, propertyLapCount, includeVitaWarning)

                        hdLobbyBlock = f"**   \
{propertyLobbyName} ({propertyPlayerCount}/8) // \
{propertyTrack} // \
{propertySpeedClass} {propertyGameMode}{listingLapCount}\
{propertyMiscSettings}**\
\n-# ‎   <t:{propertyCreateDate}:R>; {weaponAddendum}\
{playerListPrintable}\
{progressAddendum}"

                    case "Eliminator":
                        weaponAddendum = parseWeaponArray(propertyWeaponList, "Eliminator")
                        includeVitaWarning = "True" if showVitaWarning == "True" and "+Vita" in propertyPlayerList else "False"
                        progressAddendum = calculateGameProgress(propertyRaceProgress, propertyElimTarget, includeVitaWarning)

                        hdLobbyBlock = f"**   \
{propertyLobbyName} ({propertyPlayerCount}/8) // \
{propertyTrack} // \
{propertySpeedClass} {propertyGameMode} ({propertyElimTarget})\
{propertyMiscSettings}**\
\n-# ‎   <t:{propertyCreateDate}:R>; {weaponAddendum}\
{playerListPrintable}\
{progressAddendum}"

                    case "Zone Battle":
                        includeVitaWarning = "True" if showVitaWarning == "True" and "+Vita" in propertyPlayerList else "False"
                        progressAddendum = calculateGameProgress(propertyRaceProgress, propertyZBTarget, includeVitaWarning)

                        hdLobbyBlock = f"**   \
{propertyLobbyName} ({propertyPlayerCount}/8) // \
{propertyTrack} // \
{propertyGameMode} ({propertyZBTarget})\
{propertyMiscSettings}**\
\n-# ‎   <t:{propertyCreateDate}:R>\
{playerListPrintable}\
{progressAddendum}"

                    case "Tournament":
                        weaponAddendum = parseWeaponArray(propertyWeaponList, "Single Race") if propertyWeaponsEnabled == "1" else "Weapons disabled"
                        includeVitaWarning = "True" if showVitaWarning == "True" and "+Vita" in propertyPlayerList else "False"
                        progressAddendum, currentRaceNumber = calculateTourneyProgress(propertyRaceProgress, propertyLapCount, \
                        propertyTourneyTrackCount, propertyGameName, includeVitaWarning)
                        trackList = convertTourneyTrackList(propertyTournamentTrackListIDs, "HD", currentRaceNumber)

                        hdLobbyBlock = f"**   \
{propertyLobbyName} ({propertyPlayerCount}/8) // \
{propertyTourneyTrackCount} Race {propertySpeedClass} {propertyGameMode}{listingLapCount}\
{propertyMiscSettings}**\
\n-# ‎   <t:{propertyCreateDate}:R>; {weaponAddendum}\
\n-# ‎   {trackList}\
{playerListPrintable}\
{progressAddendum}"

                    case _:
                        hdLobbyBlock = "\n! Parsing error.\n"
                        logging.warning("[fetchLobbyList] Error while parsing HD XML!")
            
                parsingResultsHD = f"{parsingResultsHD}\n{hdLobbyBlock}\n"

                # ---###--- HD LOBBY DONE ---###---


            case "20794": # parse pulse lobbies


                # ---###--- WIPEOUT PULSE PARSING START ---###---


                propertyTournamentTrackListIDs = []

                propertyTrack = convertPulseGameLevelToName(lobby.attrib["GameLevel"])
                propertyGameMode = convertPulseRulesetToMode(lobby.attrib["RuleSet"])
                propertySpeedClass, propertyDefaultLapCount = convertPlayerSkillToClass(lobby.attrib["PlayerSkillLevel"])
                propertyPlayerList = lobby.attrib["PlayerListCurrent"]
                propertyLobbyName = lobby.attrib["GameName"]
                propertyPlayerCount = lobby.attrib["PlayerCount"]
                propertyMaximumPlayerCount = lobby.attrib["MaxPlayers"]

                for stats in lobby.findall('GameStats'):
                    for config in stats:
                        if(config.tag == "Weapons"):
                            propertyWeaponsEnabled = "// Weapons off" if config.text == "0" else ""
                        if(config.tag == "TrackList"):
                            for bitmask in config:
                                propertyTournamentTrackListIDs.append(bitmask.text)
                        if(config.tag == "RaceInProgress"):
                            propertyRaceInProgress = "\n**   >> RACE IN PROGRESS... HOLD ON! <<**\n-# ‎   When a Pulse race is ongoing, the lobby is hidden in-game. Please be patient!" if config.text == "1" else ""

                # ---###--- ASSEMBLE PULSE LOBBY BLOCK ---###---


                playerListPrintable = convertPlayerList(propertyPlayerList, "pulse")

                match propertyGameMode:
                    case "Single Race" | "Head to Head" | "Eliminator":
                        pulseLobbyBlock = f"\
**   {propertyLobbyName} ({propertyPlayerCount}/{propertyMaximumPlayerCount}) \
// {propertyTrack} \
// {propertySpeedClass} {propertyGameMode} \
{propertyWeaponsEnabled}** \
{playerListPrintable}\
{propertyRaceInProgress}"

                    case "Tournament":
                        trackList = convertTourneyTrackList(propertyTournamentTrackListIDs, "Pulse")
                        pulseLobbyBlock = f"\
**   {propertyLobbyName} ({propertyPlayerCount}/{propertyMaximumPlayerCount}) \
// {propertySpeedClass} {propertyGameMode} \
{propertyWeaponsEnabled}**\
\n-# ‎   {trackList} \
{playerListPrintable}\
{propertyRaceInProgress}"

                    case _:
                        pulseLobbyBlock = "\n! Parsing error.\n"
                        logging.warning("[fetchLobbyList] Error while parsing Pulse XML!")

                parsingResultsPulse = f"{parsingResultsPulse}\n{pulseLobbyBlock}\n"


                # ---###--- PULSE LOBBY DONE ---###---


            case _:
                logging.info("Unknown AppId on listing, ignoring...")


    # ---###--- PARSING IS DONE, COMPOSING INTO FINAL OUTPUT ---###---

    # ...but first, let's nuke the tourney dict, just in case (see this function's start for explanation)

    if tourneyProgressFunctionIsIdle == "True" and tourneyProgressByLobby:
        tourneyProgressByLobby.clear()

    if parsingResultsPulse == "" and parsingResultsHD != "":
        return(f"\nLobby listing (HD):{parsingResultsHD}")
    elif parsingResultsPulse != "" and parsingResultsHD == "":
        return(f"\nLobby listing (Pulse):{parsingResultsPulse}")
    elif parsingResultsHD == "" and parsingResultsPulse == "":
        return "No lobbies are up."
    else:
        return(f"\nLobby listing (HD):{parsingResultsHD}\nLobby listing (Pulse):{parsingResultsPulse}")

def fetchPlayerCount():
    xmlData = requests.get(urlCount)
    isSameFlag = "False"

    try:
        root = ET.fromstring(xmlData.content)
    except ET.ParseError:
        logging.warning("[Player Count XML Parser] Bad XML passed")
        return "failureApiFault", None
    
    playerCount = root.attrib["totalEntries"]

    xmlHash = hashlib.sha1(xmlData.content).hexdigest()
    if xmlHash == workspacePull("players"):
        isSameFlag = "True"
    else: 
        workspaceStore(xmlHash, "players")

    return ("1 player is currently logged in.", isSameFlag) if playerCount == "1" else ("!NOPLAYERS", isSameFlag) if playerCount == "0" else (f"{playerCount} players are currently logged in.", isSameFlag)
