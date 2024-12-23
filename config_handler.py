# Guess from the file name what this is.
# If you guessed "config handler" - you're incorrect! It actually does *all* of the bot's IO.
import json
import os.path
import logging
import re

def configCreate():
    configInitial = { 
        "guildID" : "0",
        "statusMessageChannelID" : "0",
        "zgrRolePing" : "0",
        "defaultBackendStatus" : "online",
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
        "experimentalFeatures" : "False"
    }
    with open("./external/config.json", "w", encoding="utf-8") as configJsonFile:
        json.dump(configInitial, configJsonFile, ensure_ascii=False, indent=4)
    print("Fill in config now.")
    exit()

def configPull(elementName):
    try:
        with open("./external/config.json", "r") as configJsonFile:
            configFile = json.load(configJsonFile)
            return configFile[elementName]
    except FileNotFoundError:
        configCreate()
    except:
        print("No such variable in config or unable to parse JSON")
        return "null"

def tokenPull():
    with open("./external/credentials.txt", "r") as tokenFile:
        return(tokenFile.read())

def workspaceStore(data, dataType):
    match dataType:
        case "lobbies":
            pattern = "hashAPILobby: "
        case "players":
            pattern = "hashAPIPlayers: "
        case "status":
            pattern = "backendStatus: "

    with open("./external/holocorp.workspace", "r+") as workspaceFile:
            workspace = workspaceFile.read()
            workspace = re.sub(rf"{pattern}\w+", f"{pattern}{data}", workspace)
            workspaceFile.seek(0)
            workspaceFile.write(workspace)
            workspaceFile.truncate()

def workspacePull(dataType):
    match dataType:
        case "lobbies":
            pattern = "hashAPILobby: "
        case "players":
            pattern = "hashAPIPlayers: "
        case "status":
            pattern = "backendStatus: "

    try:
        with open("./external/holocorp.workspace", "r") as workspaceFile:
            workspace = workspaceFile.read()
            match = re.search(rf"{pattern}(\w+)", workspace)
            return match.group(1)
    except:
        logging.warning("[Config Handler, workspacePull] Something went wrong, please investigate.")
        exit()

def messageTemplate(templateType):
    if templateType == "weeklies": templateFileName = "event_gen_template.md"
    else: templateFileName = f"status_template_{templateType}.md"
            
    try:
        with open(f"./external/message_templates/{templateFileName}", "r") as templateFile:
            return templateFile.read()
    except:
        logging.warning(f"[Config Handler, messageTemplate, {templateType}] Template missing or invalid.")
        return("missingTemplateError")