# Guess from the file name what this is.
import json
import os.path
import logging
import re
from distutils.util import strtobool
from enum import Enum

class ioScopes(Enum):
    replies = "./external/message_templates/ping_reply_list.md"
    config = "./external/config.json"

    md = "./external/message_templates/"
    llm = "./external/llm_resources/"
    secret = "./external/secrets/"

def configCreate():
    configInitial = { 
        "guildID" : "0",
        "statusMessageChannelID" : "0",
        "zgrRolePing" : "0",
        "defaultBackendStatus" : "online",
        "defaultPingReplyMode": "dumb",
        "showVitaRegion" : "False",
        "emojiVitaFlagID" : "0",
        "emojiDebugFlagID" : "0",
        "showVitaWarning" : "True",
        "apiPollRate" : "30",
        "apiLobbiesURL" : "http://svo.agracingfoundation.org/medius_db/api/GetLobbyListing",
        "apiPlayersURL" : "http://svo.agracingfoundation.org/medius_db/api/GetPlayerCount",
        "pulsePlayerListPrefix" : "-> ",
        "pulseShowRegions" : "False",
        "platformLabelPSP" : "(PSP)",
        "platformLabelPPSSPP" : "(PPSSPP)",
        "platformLabelPS3" : "(PS3)",
        "platformLabelVita" : "(Vita)",
        "platformLabelRPCS3" : "(RPCS3)",
        "llmMaxUserMessageCount": "50",
        "experimentalFeatures" : "False",
        "loggingLevel" : "Info"
    }
    with open(ioScopes.config.value, "w", encoding="utf-8") as file:
        json.dump(configInitial, file, ensure_ascii=False, indent=4)
    logging.critical("[configCreate] New config file created! Please populate it and restart.")
    exit()



def ioRead(scope: ioScopes, target: str = None):
    """ 
    Fetch data from an external file specified by the `scope`.

    This function behaves differently based on the `scope` passed:
        - ioScopes.config: 
            Reads ioScopes.config.value as a JSON file and returns the requested key value (`target`) in its most appropriate format (str | int | bool).
            - `target` value is required and must be an existing key within the ioScopes.config.value JSON.

        - ioScopes.replies: 
            Reads ioScopes.replies.value as a string, splits the contents (separator is `|||`) and returns the resulting dict. 
            - `target` argument is ignored.

        - ioScopes.md, ioScopes.llm, ioScopes.secret: 
            Reads `target` file at `ioScopes.*.value`:
            - Returns file contents as a JSON object (if file format is JSON);
            - Returns file contents as a string (if file format is anything besides JSON).
            - `target` argument is required and must be the full file name.

    Args:
        scope (ioScopes): Specifies the external file path or directory.
        target (str): Specifies the value or the file which data should be pulled from.

    Returns:
        str | int | bool | dict: as described above.
    """

    if target is None and scope.name != "replies":
        logging.error("[ioRead] No `target` passed.")
        raise TypeError(f"[ioRead] The 'target' argument is required for the '{scope.name}' scope.")

    match scope.name:
        case "config":
            try:
                with open(scope.value, "r") as file:
                    fileAsObject = json.load(file)
                configElement = fileAsObject[target]
                try:
                    return int(configElement)
                except ValueError:
                    try:
                        return bool(strtobool(configElement))
                    except ValueError:
                        return configElement

            except FileNotFoundError:
                logging.warning("[ioRead] Config file not found, making one now...")
                configCreate()
                return

            except Exception as e:
                logging.error("[configPull] No such variable in config or unable to parse JSON")
                raise e


        case "replies":
            try:
                with open(scope.value, "r") as file:
                    replyList = file.read()

                replyList = replyList.split("|||")
                return [reply.strip() for reply in replyList]

            except Exception as e:
                logging.warning(f"[loadReplies] Something went wrong, please investigate.")
                raise e


        case "md" | "llm" | "secret":
            try:
                with open(f"{scope.value}{target}", "r") as file:
                    return json.load(file) if ".json" in target else file.read()
            except FileNotFoundError as e:
                logging.warning(f"[ioRead, {scope.name}] File {scope.value}{target} not found!")
                raise e

        
        case _:
            logging.warning(f"[ioRead] Unknown scope: {scope}")