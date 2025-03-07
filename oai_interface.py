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

def databankLookup(topic):
    match topic:
        case "AGRF":
            return "The AGRF is a group ran by the FX350 pilot community. Its coowners are ThatOneBonk (aka Yuri) and ChaCheeChoo (aka Exla)."
        case "FX350":
            return "FX350 is the official Antigravity Racing League backed by the Belmondo Foundation. 12 teams participate."

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
            "description": "Look up information stored in the databank for lore-related questions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "enum": ["AGRF", "FX350"],
                        "description": "Specify which topic to look up information on. Pick the most relevant topic to the conversation.",
                    }
                },
                "required": ["topic"],
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
                tool_query_string = json.loads(tool_calls[0].function.arguments)['topic']
                results = databankLookup(tool_query_string)
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

            # remove old tool runs from context - FIXME removing all tool run context immediately isn't a good idea
            llmStates.llmContext.pop(len(llmStates.llmContext)-2)
            llmStates.llmContext.pop(len(llmStates.llmContext)-1)

    else: 
        finalResponse = modelResponse.choices[0].message.content

    llmStates.llmContext.append({"role": "assistant", "content": finalResponse})

    if len(llmStates.llmContext) > llmStates.llmContextPermanentEntryCount + llmStates.llmMaxUserMessageCount:
        logging.debug(f"[llmFetchResponse] Exceeded {llmStates.llmMaxUserMessageCount} user messages, popping the oldest...")
        llmStates.llmContext.pop(llmStates.llmContextPermanentEntryCount)

    return finalResponse