from db_handler import getEntryContent

from states import volatileStateSet
from states import llmStateSet

from io_handler import ioScopes
from io_handler import ioRead

from openai import OpenAI
import logging
import json

try:
    apiKey = ioRead(ioScopes.secret, "oai_credentials.txt")
except FileNotFoundError:
    logging.info(f"[oai_interface Initialization] OAI secret file not found, LLM replies are disabled now.")
    apiKey = None

if apiKey:
    oai_client = OpenAI(api_key=apiKey)

llmStates = llmStateSet()
volatileStates = volatileStateSet()

def getPostedLobbyListing():
    return volatileStates.statusMessageCache

if ioRead(ioScopes.config, "experimentalFeatures"):
    def databankLookup(entry: str) -> str:
        if entry == "NoRelevantEntries":
            entryContent = "The databank doesn't have a relevant entry yet."
        else:
            entryContent = getEntryContent(entry)

        if entryContent == "NoEntry" or entryContent == "EntryGone":
            return "The requested entry does not exist. Ask to notify a staff member."

        return entryContent

else:
    def databankLookup():
        return "Databank access is currently restricted."

tools = [
    {
        "type": "function",
        "function": {
            "name": "getPostedLobbyListing",
            "description": "Get the current list of pilots who are using Thallium+Beat.",
            "parameters": {
                "type": "object",
                "properties": {}
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "databankLookup",
            "description": "Look up information stored in the databank for lore-related questions. If there isn't a relevant entry in the databank, pick the respective option and admit to user.",
            "parameters": {
                "type": "object",
                "properties": {
                    "entry": {
                        "type": "string",
                        "enum": volatileStates.dbEntriesList,
                        "description": "Specify the entry you want information about. Pick the most relevant entry name to the conversation.",
                    }
                },
                "required": ["entry"],
            },
        }
    },
]

def llmFetchResponse(message: str, author: str):
    
    if not "oai_client" in globals():
        return "Sorry, LLM replies aren't available at this time. Please contact staff."

    newMessage = {"role": "user", "content": f"{author}: {message}"}
    llmStates.llmContext.append(newMessage)

    if len(message) > 30:
        logging.debug(f"[llmFetchResponse] New message is [{message[:30]}...]")
    else: # OCD
        logging.debug(f"[llmFetchResponse] New message is [{message}]")

    modelResponse = oai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=llmStates.llmContext,
        tools=tools,
        tool_choice="auto"
    )

    responseContent = modelResponse.choices[0].message 
    llmStates.llmContext.append(responseContent)

    logging.debug(f"[llmFetchResponse] Model response is {responseContent}")

    tool_calls = responseContent.tool_calls

    if tool_calls:
        tool_call_id = tool_calls[0].id
        tool_function_name = tool_calls[0].function.name

        skipToolRun = False

        match tool_function_name:
            case "getPostedLobbyListing":
                results = getPostedLobbyListing()

            case "databankLookup":
                entry = json.loads(tool_calls[0].function.arguments)['entry']
                results = databankLookup(entry)

            case _:
                logging.warning(f"[llmFetchResponse function run] Function {tool_function_name} does not exist")
                skipToolRun = True

        if not skipToolRun:
            llmStates.llmContext.append({
                "role":"tool", 
                "tool_call_id":tool_call_id, 
                "name": tool_function_name, 
                "content":results
            })

            modelResponseWithFunctionCall = oai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=llmStates.llmContext,
            )
            finalResponse = modelResponseWithFunctionCall.choices[0].message.content

    else: 
        finalResponse = modelResponse.choices[0].message.content

    llmStates.llmContext.append({"role": "assistant", "content": finalResponse})

    if len(llmStates.llmContext) > llmStates.llmContextPermanentEntryCount + llmStates.llmMaxUserMessageCount:
        logging.debug(f"[llmFetchResponse] Exceeded {llmStates.llmMaxUserMessageCount} user messages, popping the oldest...")

        for i in range (1,6):
            llmStates.llmContext.pop(llmStates.llmContextPermanentEntryCount)
            try:
                role = llmStates.llmContext[llmStates.llmContextPermanentEntryCount]["role"]
            except:
                role = "assistant"
            if role == "user":
                break

    return finalResponse