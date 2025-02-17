from openai import OpenAI
from io_handler import llmKeyPull
from states import llmStateSet
from states import volatileStateSet
import logging
import json

client = OpenAI(api_key=llmKeyPull())

llmStates = llmStateSet()
volatileStates = volatileStateSet()

def getPostedLobbyListing():
    return volatileStates.statusMessageCache

tools = [{
    "type": "function",
    "function": {
        "name": "getPostedLobbyListing",
        "description": "Get the current list of pilots who are using Thallium+Beat.",
        "parameters": {
            "type": "object",
            "properties": {}
        }
    }
}]

def llmFetchResponse(message: str, author: str):
    
    newMessage = {"role": "user", "content": f"{author}: {message}"}
    llmStates.llmContext.append(newMessage)

    logging.debug(f"[llmFetchResponse] New message is {message[:30]}...")

    modelResponse = client.chat.completions.create(
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

        if tool_function_name == 'getPostedLobbyListing':
            results = getPostedLobbyListing()

            llmStates.llmContext.append({
                "role":"tool", 
                "tool_call_id":tool_call_id, 
                "name": tool_function_name, 
                "content":results
            })

            modelResponseWithFunctionCall = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=llmStates.llmContext,
            )
            finalResponse = modelResponseWithFunctionCall.choices[0].message.content

            # remove old tool runs from context
            llmStates.llmContext.pop(len(llmStates.llmContext)-2)
            llmStates.llmContext.pop(len(llmStates.llmContext)-1)
        else: 
            logging.warning(f"[llmFetchResponse function run] Function {tool_function_name} does not exist")

    else: 
        finalResponse = modelResponse.choices[0].message.content

    llmStates.llmContext.append({"role": "assistant", "content": finalResponse})

    if len(llmStates.llmContext) > llmStates.llmContextPermanentEntryCount + llmStates.llmMaxUserMessageCount:
        logging.debug(f"[llmFetchResponse] Exceeded {llmStates.llmMaxUserMessageCount} user messages, popping the oldest...")
        llmStates.llmContext.pop(llmStates.llmContextPermanentEntryCount)

    return finalResponse