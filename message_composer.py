# This function takes the XML parser outputs and combines them into a single string that can be used in the status message.
import logging
import string

from xml_parser import playerListingAssembler
from xml_parser import lobbyListingAssembler
from xml_parser import xmlToValues

from states import volatileStateSet
from states import firmStateSet

from io_handler import ioScopes
from io_handler import ioRead

volatileStates = volatileStateSet()
firmStates = firmStateSet()

def composeStatus() -> str:
    """
    Componses a complete status message from online status templates and parsed API output.
    The message is stored in the `statusMessageText` variable of the firmStateSet class (singleton).

    Args:
        None.

    Returns:
        str: status code:
            - nothingToDo: Both API outputs haven't changed since the last update, and the status message shouldn't be updated.
            - failure: There has been a problem with parsing API output.
            - updated: A new message has been successfully composed and it is now stored in the firmStateSet.statusMessageText variable.
    """
    try:
        # FIXME this is for testing
        #fetchedLobbyList = lobbyListingAssembler(xmlToValues(firmStates.urlListing))
        fetchedLobbyList = lobbyListingAssembler(xmlToValues("../GetLobbyListing.xml"))
        #fetchedPlayerList = playerListingAssembler(xmlToValues(firmStates.urlCount))
        fetchedPlayerList = playerListingAssembler(xmlToValues("../GetPlayerCount.xml"))
    except Exception as e:
        firmStates.statusMessageText = ioRead(ioScopes.md, "status_failure.md")
        logging.error(f"[composeStatus] Got an Exception: {e}, setting status to `status_failure.md`")
        return "failure"

    if fetchedLobbyList == None and fetchedPlayerList[0] == None:
        return "nothingToDo"

    playerListOutput = volatileStates.playerListing
    lobbyListOutput = volatileStates.lobbyListing

    if fetchedPlayerList[0] != None:
        playerListing, playerCount = fetchedPlayerList
        playerListOutput = ""

        # TODO make this an element
        if playerCount == 0:
            playerListOutput = "!NOPLAYERS"
        elif playerCount == 1:
            playerListOutput += "1 player is currently logged in."
        else:
            playerListOutput += f"{playerCount} players are currenty logged in."

        if playerListing:
            playerListOutput += f"\n-# {playerListing}"

        volatileStates.playerListing = playerListOutput

    if fetchedLobbyList != None:
        lobbyList = fetchedLobbyList
        # do all the lobby shit here...
        # sort by appId and put it into lobbyList

        pulseLobbies = ""
        hdLobbies = ""

        for lobby in lobbyList["23360"]:
            hdLobbies += lobby + "\n\n"
        for lobby in lobbyList["20794"]:
            pulseLobbies += lobby + "\n\n"

        # TODO make this an element
        if hdLobbies:
            hdLobbies = f"Lobby lising (HD):\n{hdLobbies.strip()}"

        if pulseLobbies:
            pulseLobbies = f"Lobby listing (Pulse):\n{pulseLobbies.strip()}"

        lobbyListOutput = f"{hdLobbies}\n\n{pulseLobbies}".strip()
        lobbyListOutput = f"\n{lobbyListOutput}"

    firmStates.statusMessageText = ioRead(ioScopes.md, "status_online.md")\
    .replace("!PLAYERCOUNT", playerListOutput)\
    .replace("!LOBBYLISTING", lobbyListOutput)\
    .replace("!NOPLAYERS\n", "")
    return "updated"


# FIXME i do not like this structure, nor do i like the structure of holocorp.py





# def composeStatus() -> str:
#     """
#     Componses a complete status message from online status templates and parsed API output.
#     The message is stored in the `statusMessageText` variable of the firmStateSet class (singleton).

#     Args:
#         None.

#     Returns:
#         str: status code:
#             - nothingToDo: Both API outputs haven't changed since the last update, and the status message shouldn't be updated.
#             - failure: There has been a problem with parsing API output.
#             - updated: A new message has been successfully composed and it is now stored in the firmStateSet.statusMessageText variable.
#     """
#     fetchedLobbyList = fetchLobbyList()

#     if "failureApiFault" in fetchedLobbyList:
#         firmStates.statusMessageText = ioRead(ioScopes.md, "status_failure.md")
#         logging.info("[composeStatus] Got a `failureApiFault`, setting status to `status_failure.md`")
#         return "failure"

#     if fetchedLobbyList != "nothingToDo":
#         volatileStates.lobbyListing = fetchedLobbyList  # this should ensure that we always have the current listing in memory and that it doesn't get
#         volatileStates.lobbyListingIsSame = False       # overwritten when that's not needed
#     else:
#         volatileStates.lobbyListingIsSame = True

#     playerCount, volatileStates.playerCountIsSame = fetchPlayerCount()


#     if volatileStates.lobbyListingIsSame == True and volatileStates.playerCountIsSame == True:
#         return "nothingToDo"
#     else:
#         firmStates.statusMessageText = ioRead(ioScopes.md, "status_online.md")\
#         .replace("!PLAYERCOUNT", playerCount)\
#         .replace("!LOBBYLISTING", volatileStates.lobbyListing)\
#         .replace("!NOPLAYERS\n", "")
#         return "updated"
