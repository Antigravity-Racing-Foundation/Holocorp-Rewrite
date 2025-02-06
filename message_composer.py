# This function takes the XML parser output and combines them into a single string that can be put straight on the status message
# or ignored entirely. It may seem unnecessary to offload this to a dedicated file, but the nigthmares of Holocorp Classic
# haunted into making this a dedicated file.
from io_handler import *
from xml_parser import *
import string
from logging import *
from states import volatileStateSet

volatileStates = volatileStateSet()

def composeStatus():

    fetchedLobbyList = fetchLobbyList()
    if fetchedLobbyList != "nothingToDo":
        volatileStates.lobbyListing = fetchedLobbyList  # this should ensure that we always have the current listing in memory and that it doesn't get
        volatileStates.lobbyListingIsSame = False                      # overwritten when that's not needed
    else:
        volatileStates.lobbyListingIsSame = True

    playerCount, volatileStates.playerCountIsSame = fetchPlayerCount()


    if volatileStates.lobbyListingIsSame == True and volatileStates.playerCountIsSame == True:
        return "nothingToDo"
    else:
        return messageTemplate("online").replace("!PLAYERCOUNT", playerCount)\
        .replace("!LOBBYLISTING", volatileStates.lobbyListing)\
        .replace("!NOPLAYERS\n", "")