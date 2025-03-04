# This function takes the XML parser outputs and combines them into a single string that can be used in the status message.
from xml_parser import fetchPlayerCount
from xml_parser import fetchLobbyList

from states import volatileStateSet
from states import firmStateSet

from io_handler import ioScopes
from io_handler import ioRead

import logging
import string

volatileStates = volatileStateSet()
firmStates = firmStateSet()

def composeStatus():

    fetchedLobbyList = fetchLobbyList()

    if "failureApiFault" in fetchedLobbyList:
        firmStates.statusMessageText = ioRead(ioScopes.md, "status_failure.md")
        logging.info("[composeStatus] Got a `failureApiFault`, setting status to `status_failure.md`")
        return "failure"

    if fetchedLobbyList != "nothingToDo":
        volatileStates.lobbyListing = fetchedLobbyList  # this should ensure that we always have the current listing in memory and that it doesn't get
        volatileStates.lobbyListingIsSame = False       # overwritten when that's not needed
    else:
        volatileStates.lobbyListingIsSame = True

    playerCount, volatileStates.playerCountIsSame = fetchPlayerCount()


    if volatileStates.lobbyListingIsSame == True and volatileStates.playerCountIsSame == True:
        return "nothingToDo"
    else:
        firmStates.statusMessageText = ioRead(ioScopes.md, "status_online.md")\
        .replace("!PLAYERCOUNT", playerCount)\
        .replace("!LOBBYLISTING", volatileStates.lobbyListing)\
        .replace("!NOPLAYERS\n", "")
        return "updated"