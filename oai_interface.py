from db_handler import getEntriesByTopic
from db_handler import getEntryContent
from db_handler import getTopics

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

    def databankLookup(topic: str, entry: str) -> str:
        entryContent = getEntryContent(topic, entry)
        if not entryContent:
            return "This entry within this topic does not exist."
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
            "description": "Look up information stored in the databank for lore-related questions. If an entry doesn't exist within a topic, ask user for a clarification on what they mean.",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "enum": volatileStates.dbTopicList,
                        "description": "Specify which topic to look up information on. Pick the most relevant topic to the conversation and the entry you wish to look up.",
                    },
                    "entry": {
                        "type": "string",
                        "enum": volatileStates.dbEntriesList,
                        "description": "Specify the entry you want information about. Pick the most relevant entry name to the conversation as well as the topic it likely belongs to.",
                    }
                },
                "required": ["topic", "entry"],
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
                topic = json.loads(tool_calls[0].function.arguments)['topic']
                entry = json.loads(tool_calls[0].function.arguments)['entry']

                # this is so that if the model confuses a team for an organization, it's automatically corrected
                if entry in volatileStates.dbTeamNames:
                    topic = "Teams"

                results = databankLookup(topic, entry)

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