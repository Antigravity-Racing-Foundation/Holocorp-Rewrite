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

            "pingReplyType": ioRead(ioScopes.config, "defaultPingReplyMode"),
            "pingRepliesRigged": False,
            "pingReplies": ioRead(ioScopes.replies),
            "pingReplyRiggedMessage": "None",
            "currentStatusAlreadyPosted": "None",
            "statusMessageCache": "None",
            "pingReplyCache": [],
            "trackGeneratorCache": [], # entrypoint states

            "dbTopicList": None,
            "dbEntriesList": None,
            "dbTeamNames": None # databank states
        }
        self.__dict__.update(self._defaults)

        from db_handler import getEntriesByTopic
        from db_handler import getTopics

        topicList = []
        for entry in getTopics():
            topicList.append(entry["name"])

        # FIXME THIS IS HORRIBLE FOR PERFORMANCE
        allEntries = []
        teamEntries = []
        for topic in topicList:
            for entry in getEntriesByTopic(topic):
                allEntries.append(entry["name"])
                if topic == "Teams":
                    teamEntries.append(entry["name"])

        self.dbTopicList = topicList
        self.dbEntriesList = allEntries
        self.dbTeamNames = teamEntries

@singleton
class firmStateSet:
    def __init__(self):
        self.reset()

    def reset(self):
        self._defaults = {
            "urlListing": ioRead(ioScopes.config, "apiLobbiesURL"),
            "urlCount": ioRead(ioScopes.config, "apiPlayersURL"),
            "showVitaWarning": ioRead(ioScopes.config, "showVitaWarning"),
            "vitaFlag": ioRead(ioScopes.config, "emojiVitaFlagID"),
            "debugFlag": ioRead(ioScopes.config, "emojiDebugFlagID"),
            "showVitaRegion": ioRead(ioScopes.config, "showVitaRegion"),

            "platformLabelPSP": ioRead(ioScopes.config, "platformLabelPSP"),
            "platformLabelPPSSPP": ioRead(ioScopes.config, "platformLabelPPSSPP"),
            "platformLabelPS3": ioRead(ioScopes.config, "platformLabelPS3"),
            "platformLabelVita": ioRead(ioScopes.config, "platformLabelVita"),
            "platformLabelRPCS3": ioRead(ioScopes.config, "platformLabelRPCS3"), # parser states

            "backendStatus": ioRead(ioScopes.config, "defaultBackendStatus"),
            "statusMessageText": None,
            "channel": "None",
            "trackgenDroppedTrackResetCount": ioRead(ioScopes.config, "trackgenDroppedTrackResetCount"), # entrypoint states

            "dbFilePath": ioRead(ioScopes.config, "dbFilePath"),
            "dbSchemaPath": ioRead(ioScopes.config, "dbSchemaPath") # databank states
        }
        self.__dict__.update(self._defaults)
        self.statusMessageText = ioRead(ioScopes.md, f"status_{self.backendStatus}.md")

@singleton
class llmStateSet:
    def __init__(self):
        self.reset()

    def reset(self):
        llmInitialContext = [{"role": "system", "content": ioRead(ioScopes.llm, "system_message.md")}]
        exampleMessages = ioRead(ioScopes.llm, "example_messages.json")
        llmInitialContext.extend(exampleMessages["messages"])

        self._defaults = {
            "llmContext": llmInitialContext,
            "llmContextPermanentEntryCount": len(llmInitialContext),
            # max message count is multiplied by two such that it looks at message pairs, not individual messages
            "llmMaxUserMessageCount": int(ioRead(ioScopes.config, "llmMaxUserMessageCount")) * 2
        }
        self.__dict__.update(self._defaults)