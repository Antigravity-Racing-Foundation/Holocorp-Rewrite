import ctypes
import json

xml_parser = ctypes.cdll.LoadLibrary("./xml_parser/xml_parser.so")

xml_parser.ParseListing.argtypes = [ctypes.c_char_p]
xml_parser.ParseListing.restype = ctypes.c_char_p

# xml_parser.ParsePlayers.argtypes = [ctypes.c_char_p]
# xml_parser.ParsePlayers.restype = ctypes.c_char_p

urlListing = "http://svo.agracingfoundation.org/medius_db/api/GetLobbyListing"

def fetchLobbyList(url: str) -> str:
    apiJson = json.loads(xml_parser.ParseListing(str.encode(url)).decode("utf-8"))
    if apiJson:
        returnString = ""
        for entry in apiJson:
            print(entry["AppId"])
        return returnString
    else:
        return "No lobbies"

# def fetchPlayerCount(url: str) -> str:
#     return xml_parser.ParsePlayers(str.encode(url)).decode("urf-8")