# This function takes the XML parser output and combines them into a single string that can be put straight on the status message
# or ignored entirely. It may seem unnecessary to offload this to a dedicated file, but the nigthmares of Holocorp Classic
# haunted into making this a dedicated file.
from config_handler import *
from xml_parser import *
import string
from logging import *

global lobbyListing
lobbyListing = ""

def composeStatus():
    global lobbyListing

    fetchedLobbyList = fetchLobbyList()
    if fetchedLobbyList != "nothingToDo":
        lobbyListing = fetchedLobbyList # this should ensure that we always have the current listing in memory and that it doesn't get
        lobbyListingIsSame = False    # overwritten when that's not needed
    else:
        lobbyListingIsSame = True

    playerCount, playerCountIsSame = fetchPlayerCount()


    if lobbyListingIsSame == True and playerCountIsSame == True:
        return "nothingToDo"
    else:
        return messageTemplate("online").replace("!PLAYERCOUNT", playerCount)\
        .replace("!LOBBYLISTING", lobbyListing)\
        .replace("!NOPLAYERS\n", "")