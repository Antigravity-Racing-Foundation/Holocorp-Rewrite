# This is the point where I go pro (or something)

from io_handler import *

def singleton(cls): # singleton boilerplate
    instances = {}

    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return get_instance

@singleton
class volatileStateSet:
    def __init__(self):
        self.reset()
    
    def reset(self):
        self._defaults = {
            "hashAPILobby": "None",
            "hashAPIPlayers": "None",
            "appId": "None",  # TODO: test if appId has to be a volatileState
            "tourneyProgressByLobby": {}, # this dict will have lobby name as key, current race, last update and tourney finished flag
            "tourneyProgressFunctionIsIdle": False, # parser states

            "playerCountIsSame": False,
            "lobbyListingIsSame": False,
            "lobbyListing": "None", # message_composer states

            "pingRepliesEnabled": True,
            "pingRepliesRigged": False,
            "pingReplies": loadReplies(),
            "pingReplyRiggedMessage": "None",
            "currentStatusAlreadyPosted": "None",
            "statusMessageCache": "None",
            "pingReplyCache": [],
            "trackGeneratorCache": [] # entrypoint states
        }
        self.__dict__.update(self._defaults)

@singleton
class firmStateSet:
    def __init__(self):
        self.reset()

    def reset(self):
        self._defaults = {
            "urlListing": configPull("apiLobbiesURL"),
            "urlCount": configPull("apiPlayersURL"),
            "showVitaWarning": configPull("showVitaWarning"),
            "vitaFlag": configPull("emojiVitaFlagID"),
            "debugFlag": configPull("emojiDebugFlagID"),
            "showVitaRegion": configPull("showVitaRegion"),

            "platformLabelPSP": configPull("platformLabelPSP"),
            "platformLabelPPSSPP": configPull("platformLabelPPSSPP"),
            "platformLabelPS3": configPull("platformLabelPS3"),
            "platformLabelVita": configPull("platformLabelVita"),
            "platformLabelRPCS3": configPull("platformLabelRPCS3"), # parser states

            "backendStatus": configPull("defaultBackendStatus"),
            "channel": "None" # entrypoint states
        }
        self.__dict__.update(self._defaults)