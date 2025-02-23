# Guess from the file name what this is.
import json
import os.path
import logging
import re
from distutils.util import strtobool

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
    with open("./external/config.json", "w", encoding="utf-8") as configJsonFile:
        json.dump(configInitial, configJsonFile, ensure_ascii=False, indent=4)
    print("Fill in config now.")
    exit()

def configPull(elementName):
    try:
        with open("./external/config.json", "r") as configJsonFile:
            configFile = json.load(configJsonFile)
            configElement = configFile[elementName]
            try:
                return bool(strtobool(configElement))
            except ValueError:
                return configElement
    except FileNotFoundError:
        configCreate()
    except:
        logging.error("[configPull] No such variable in config or unable to parse JSON")
        return "null"

def tokenPull():
    with open("./external/credentials.txt", "r") as tokenFile:
        return(tokenFile.read())
        
def llmKeyPull():
    with open("./external/llm_resources/oai_credentials.txt", "r") as keyFile:
        return(keyFile.read())

# TODO: review all of this mess, there's definiely a much nicer way of handling all of this

def llmResourcePull(resourceName):
    try:
        with open(f"./external/llm_resources/{resourceName}", "r") as resourceFile:
            returnFunction = json.load(resourceFile) if ".json" in resourceName else resourceFile.read()
            return returnFunction
    except:
        logging.warning(f"[llmResourcePull, {resourceName}] Resource missing or invalid.")
        return("An invalid template has been passed to you. You should tell the user about it and ask a developer to fix this. No operations should take place, reply as concise as possible.")

def messageTemplate(templateType):
    if templateType == "weeklies": templateFileName = "event_gen_template.md"
    else: templateFileName = f"status_template_{templateType}.md"
            
    try:
        with open(f"./external/message_templates/{templateFileName}", "r") as templateFile:
            return templateFile.read()
    except:
        logging.warning(f"[messageTemplate, {templateType}] Template missing or invalid.")
        return("Missing template")

def loadReplies():
    try:
        with open(f"./external/message_templates/ping_reply_list.md", "r") as replyListFile:
            replyList = replyListFile.read()
        replyList = replyList.split("|||")
        return [reply.strip() for reply in replyList]
    except:
        logging.warning(f"[loadReplies] Something went wrong, please investigate.")