# This is the entry point for the bot. This file does the Discord API handling.

# TODO: implement available lobby spots reminder
# TODO: pull as much ui text as possible from .md templates
# TODO: event pre-ping feature

from distutils.util import strtobool
from pathlib import Path
import datetime
import discord
import logging
import asyncio
import random
import sys
import re
import os
import io

from discord.ext.commands import MissingPermissions
from discord import app_commands
from discord.ext import commands
from discord.ext import tasks

from event_list_generate import generateRandomTrack
from event_list_generate import generateEventList
from oai_interface import llmFetchResponse
from message_composer import *
from io_handler import *

from states import volatileStateSet
from states import firmStateSet
from states import llmStateSet

volatileStates = volatileStateSet()
firmStates = firmStateSet()
llmStates = llmStateSet()

intents = discord.Intents.default()
intents.message_content = True

class Client(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)

    async def setup_hook(self):
        await commandTree.sync()

client = Client(intents=discord.Intents.default())

commandTree = app_commands.CommandTree(client)

logging.basicConfig(encoding='utf-8', level=logging.NOTSET)

try:
    logging.getLogger().setLevel(logging.getLevelName(configPull("loggingLevel").upper()))
except Exception as e:
    logging.getLogger().setLevel(logging.INFO)
    logging.error(f"Logging setup failed with {e}; defaulting to INFO")


async def updateStatusMessage(desiredContent): # abstract of edit/send new message in status channel

    if volatileStates.statusMessageCache == desiredContent:
        logging.debug("[updateStatusMessage] desiredContent matches cache, aborting!")
        return("nothingToDo")
    logging.debug("[updateStatusMessage] Status message update routine started")
    existingMessageId = 0
    volatileStates.statusMessageCache = desiredContent

    async for previous_message in firmStates.channel.history(limit=2):
        if previous_message.author == client.user:
            existingMessageId = previous_message.id
            logging.debug("[updateStatusMessage] existingMessageId defined!")

    if existingMessageId == 0:
        newMessage = await firmStates.channel.send(desiredContent)
        existingMessageId = newMessage.id
        logging.info(f"[updateStatusMessage] Status message not found, new message ID: {str(existingMessageId)}")

    else:
        targetMessage = await firmStates.channel.fetch_message(existingMessageId)
        await targetMessage.edit(content=desiredContent)
        logging.debug("[updateStatusMessage] Message updated!")




async def statusMessageHandler(statusMessage): # decide what to post to updateStatusMessage

    if (firmStates.backendStatus != "online") and volatileStates.currentStatusAlreadyPosted != True:
        await updateStatusMessage(firmStates.statusMessageText)
        volatileStates.currentStatusAlreadyPosted = True
        if listLobbies.is_running() == True:
            listLobbies.stop()
            logging.debug("[statusMessageHandler] Stopped lobby listing")
    else:
        logging.debug("[statusMessageHandler] Invoking updateStatusMessage to post status...")
        await updateStatusMessage(firmStates.statusMessageText)




status_choices = [
    app_commands.Choice(name="online", value="online"),
    app_commands.Choice(name="offline", value="offline"),
    app_commands.Choice(name="maintenance", value="maintenance")
]
@commandTree.command(name="status", description="Change status message to `online`, `offline` or `maintenance`", guild=None)
@app_commands.choices(status_command=status_choices)
@app_commands.default_permissions(permissions=0)
async def status(interaction: discord.Interaction, status_command: str, reason: str = None): # set backend status command
    volatileStates.currentStatusAlreadyPosted = False # if this command is invoked, it will probably need to update the status message

    if status_command == firmStates.backendStatus:
        await interaction.response.send_message(ephemeral=True, content=f"Backend status is already `{status_command.capitalize()}`. Nothing to do.")
        return

    if status_command != "online" and reason:
        await interaction.response.send_message(ephemeral=True, content=f"Setting backend status to `{status_command.capitalize()}` with reason `{reason}`")
    else:
        await interaction.response.send_message(ephemeral=True, content=f"Setting backend status to `{status_command.capitalize()}`")

    if status_command == "online":
        firmStates.backendStatus = status_command

        volatileStates.statusMessageCache = "None"
        volatileStates.hashAPILobby = "None"
        volatileStates.hashAPIPlayers = "None"
        
        if not listLobbies.is_running(): listLobbies.start()
        
        logging.debug("[status] Cleared cache and started lobby listing routine")
    else:
        firmStates.backendStatus = status_command
        if listLobbies.is_running(): listLobbies.stop()

        if reason:
            firmStates.statusMessageText = messageTemplate(firmStates.backendStatus + "_with_reason").replace("!REASON", reason)
        else:
            firmStates.statusMessageText = messageTemplate(firmStates.backendStatus)

        await statusMessageHandler(firmStates.statusMessageText)
        logging.debug("[status] Stopped lobby listing routine")

    logging.debug("[status] New backend status is now stored in firmStates")

@status.error
async def status_error(interaction: discord.Interaction, error):
    if isinstance(error, discord.app_commands.errors.MissingPermissions):
        logging.info("[status Command Error Handler] Invoke attempted by a peasant, but perms are missing lol")
        await interaction.response.send_message(ephemeral=True, content="You don't have the permission to do this")




@commandTree.command(name="generate_events", description="Generate a weekly event list", guild=None)
@discord.app_commands.checks.has_permissions(manage_messages=True)
async def events(interaction: discord.Interaction):
    await interaction.response.send_message(ephemeral=True, content=f'here\'s your order, copyable and pastable!\n```{generateEventList()}```\n:3')

@events.error
async def events_error(interaction: discord.Interaction, error):
    if isinstance(error, discord.app_commands.errors.MissingPermissions):
        logging.info("[events Command Error Handler] Invoke attempted by a peasant, but perms are missing lol")
        await interaction.response.send_message(ephemeral=True, content="You don't have the permission to do this")
    else:
        raise(error)




game_choice = [
    app_commands.Choice(name="WipEout HD", value="hd"),
    app_commands.Choice(name="WipEout Pulse", value="pulse"),
]
binary_options = [
    app_commands.Choice(name="True", value="True"),
    app_commands.Choice(name="False", value="False"),
]
@commandTree.command(name="gimme_a_track", description="Gimme a random track, botty!", guild=None)
@commands.cooldown(1, 10, commands.BucketType.user) 

@app_commands.choices(game=game_choice)

@app_commands.describe(count="How many tracks would you like?")

@app_commands.choices(extra_tracks=binary_options)
@app_commands.describe(extra_tracks="Zone tracks for HD and DLC tracks for Pulse")

@app_commands.choices(announce=binary_options)
@app_commands.describe(announce="Tell chat?")

async def trackgen(interaction: discord.Interaction, game: str, count: int = 1, extra_tracks: str = "False", announce: str = "False"):

    logging.debug(f"[trackgen] Command invoked ({game}, {count}, extra_tracks = {extra_tracks}, announce = {announce})")

    extra_tracks = bool(strtobool(extra_tracks))
    announce = bool(strtobool(announce))

    if count < 1:
        logging.debug("[trackgen] Passed count is less than 1, aborting...")
        await interaction.response.send_message(ephemeral=True, content="no, fuck you")
        return
    elif count > 24:
        logging.debug("[trackgen] Passed count is more than 24, aborting...")
        await interaction.response.send_message(ephemeral=True, content="that's a bit too many tracks (let's not do more than 24, okay?)")
        return

    anouncement_prefix = "Our track iiiiiiis:" if count == 1 else "Our track list iiiiiiis:"

    match game:
        case "hd":
            trackRange = "hd" if extra_tracks == False else "hdZone"
        case "pulse":
            trackRange = "pulse" if extra_tracks == False else "pulseDLC"
        case _:
            logging.debug("[trackgen] Invalid game argument passed... somehow?")
            await interaction.response.send_message(ephemeral=True, content="okay i'm sorry but how the fuck did you even manage to pick an invalid option?")
            return
        
    logging.debug(f"[trackgen] Game is {trackRange}")

    trackList = ""
    for i in range (0, count):

        for attempts in range (16):
            await asyncio.sleep(0.05) # random is time-based so we sleep
            generatedTrack = generateRandomTrack(trackRange)
            if generatedTrack not in volatileStates.trackGeneratorCache:
                volatileStates.trackGeneratorCache.append(generatedTrack)
                trackList = f"{trackList}\n{generatedTrack}"
                logging.debug("[trackgen] Found valid track")
                break
        else:
            logging.debug("[trackgen] Exceeded maximum attempt count")
            trackList = f"{trackList}\n{generateRandomTrack(trackRange)}"
        
        if len(volatileStates.trackGeneratorCache) > 6:
            volatileStates.trackGeneratorCache = []
            logging.debug("[trackgen] Popping cache array (exceeded 6 elements)")

    if announce == True:
        logging.debug("[trackgen] Sending public response...")
        await interaction.response.send_message(ephemeral=False, content=f"{anouncement_prefix}\n```{trackList}!```")
    else:
        logging.debug("[trackgen] Sending private response...")
        await interaction.response.send_message(ephemeral=True, content=f"here you go :3\n```{trackList}```")




activity_choices = [
    app_commands.Choice(name="playing", value="playing"),
    app_commands.Choice(name="watching", value="watching"),
    app_commands.Choice(name="clear", value="clear")
]
@commandTree.command(name="activity", description="Set bot activity to `Playing` or `Watching` with an arbitrary name or clear it", guild=None)
@app_commands.choices(activity_type=activity_choices)
@app_commands.describe(activity_name="What are we playin?")
@app_commands.default_permissions(permissions=0)
async def activity(interaction: discord.Interaction, activity_type: str, activity_name: str = None):
    if activity_type == "clear":
        await client.change_presence(activity=None)
        await interaction.response.send_message(ephemeral=True, content=f"Presence activity cleared (dropped activity_name you might've passed)")
        return

    if activity_name == None:
        await interaction.response.send_message(ephemeral=True, content=f"Sooo what are we {activity_type}? (specify `activity_name` for non clear types dummy)")
        return

    match activity_type:
        case "playing":
            discordApiActivity = discord.Game(name=activity_name)
        case "watching":
            discordApiActivity = discord.Activity(type=discord.ActivityType.watching, name=activity_name)

    await client.change_presence(activity=discordApiActivity)
    await interaction.response.send_message(ephemeral=True, content=f"Set activity to [{activity_type.capitalize()} **{activity_name}**]")

@activity.error
async def activity_error(interaction: discord.Interaction, error):
    if isinstance(error, discord.app_commands.errors.MissingPermissions):
        logging.info("[activity Command Error Handler] Invoke attempted by a peasant, but perms are missing lol")
        await interaction.response.send_message(ephemeral=True, content="You don't have the permission to do this")



reply_choices = [
    app_commands.Choice(name="disable", value="disable"),
    app_commands.Choice(name="dumb_replies", value="dumb"),
    app_commands.Choice(name="llm_replies", value="smart"),
    app_commands.Choice(name="reload_reply_list", value="reload"),
    app_commands.Choice(name="set_next_reply", value="rig")
]
@commandTree.command(name="reply_control", description="Change, reload or rig ping reply functionality", guild=None)
@app_commands.choices(action_command=reply_choices)
@app_commands.default_permissions(permissions=0)
async def replies(interaction: discord.Interaction, action_command: str, rigged_message: str = ""):

    match action_command:
        case "disable":
            volatileStates.pingReplyType = "off"
            await interaction.response.send_message(ephemeral=True, content=f"Ping replies are disabled now!`")
            return

        case "dumb":
            volatileStates.pingReplyType = "dumb"
            await interaction.response.send_message(ephemeral=True, content=f"Botty will reply with preset messages now!")
            return

        case "smart":
            volatileStates.pingReplyType = "smart"
            await interaction.response.send_message(ephemeral=True, content=f"Botty will use the LLM now!")
            return

        case "reload":
            volatileStates.pingReplies = loadReplies()
            volatileStates.pingRepliesRigged= False
            volatileStates.pingReplyRiggedMessage = "" 
            await interaction.response.send_message(ephemeral=True, content=f"Reply list loaded!")
            return

        case "rig":
            if rigged_message == "":
                await interaction.response.send_message(ephemeral=True, content=f"am i just supposed to be silent then? use `disable` for that, dummy")
                return
            else:
                volatileStates.pingRepliesRigged = True
                volatileStates.pingReplyRiggedMessage = rigged_message
                await interaction.response.send_message(ephemeral=True, content=f"okie, next time i'll say [{rigged_message}]! (reload_reply_list to cancel)")

@replies.error
async def replies_error(interaction: discord.Interaction, error):
    if isinstance(error, discord.app_commands.errors.MissingPermissions):
        logging.info("[replies Command Error Handler] Invoke attempted by a peasant, but perms are missing lol")
        await interaction.response.send_message(ephemeral=True, content="You don't have the permission to do this")




reset_choices = [
    app_commands.Choice(name="partial", value="partial"),
    app_commands.Choice(name="llm", value="llm"),
    app_commands.Choice(name="full", value="full")
]
@commandTree.command(name="reset", description="Start from a clean slate", guild=None)
@app_commands.choices(reset_command=reset_choices)
@app_commands.default_permissions(permissions=0)
async def reset(interaction: discord.Interaction, reset_command: str):

    # FIXME: invoke status change logic on full bot reset! move the logic out of the slash command into another async function,
    # then call it in both that one and this one

    logging.info(f"[reset] A {reset_command} reset has been requested!")

    match reset_command:
        case "partial":
            volatileStates.reset()
            await interaction.response.send_message(ephemeral=True, content=f"Bot's volatile states reset!")

        case "llm":
            llmStates.reset()
            await interaction.response.send_message(ephemeral=True, content=f"LLM states reset!")
        
        case "full":
            volatileStates.reset()
            firmStates.reset()
            status(volatileStates.backendStatus)
            firmStates.channel = client.get_channel(int(configPull("statusMessageChannelID")))
            await interaction.response.send_message(ephemeral=True, content=f"Wiped everything! Fresh stuff has been pulled from config and logic has been reset.")
        
@activity.error
async def reset_error(interaction: discord.Interaction, error):
    if isinstance(error, discord.app_commands.errors.MissingPermissions):
        logging.info("[reset Command Error Handler] Invoke attempted by a peasant, but perms are missing lol")
        await interaction.response.send_message(ephemeral=True, content="You don't have the permission to do this")




if configPull("experimentalFeatures"):
    scope_choices = [
        app_commands.Choice(name="volatile_states", value="volatileStates"),
        app_commands.Choice(name="firm_states", value="firmStates"),
        app_commands.Choice(name="llm_states", value="llmStates")
    ]
    @commandTree.command(name="peek", description="Take a look inside. Exciting!", guild=None)
    @app_commands.choices(scope=scope_choices)
    @app_commands.default_permissions(permissions=0)
    async def peek(interaction: discord.Interaction, scope: str, name: str):
        try:
            returnValue = getattr(globals().get(scope), name)
        except AttributeError as e:
            logging.debug(f"[peek] Failed to fetch {name} of {scope} with {e}")
            await interaction.response.send_message(ephemeral=True, content=f"Something went wrong! You've probably requested a bad value.\n{e}")
            return
        
        if len(str(returnValue)) > 1000:
            returnValue = discord.File(io.BytesIO(str(returnValue).replace("},", "},\n").encode()), filename="trace.txt")
            await interaction.response.send_message(ephemeral=True, content="Output length exceeded 1000 characters...", file=returnValue)
            return
        await interaction.response.send_message(ephemeral=True, content=f"`{scope}.{name}` = `{returnValue}`")

    @activity.error
    async def peek_error(interaction: discord.Interaction, error):
        if isinstance(error, discord.app_commands.errors.MissingPermissions):
            logging.info("[peek Command Error Handler] Invoke attempted by a peasant, but perms are missing lol")
            await interaction.response.send_message(ephemeral=True, content="You don't have the permission to do this")



    # TODO generate scope choices by looking up class instances
    @commandTree.command(name="poke", description="Break stuff! Good time for a reminder that /reset is a thing.", guild=None)
    @app_commands.choices(scope=scope_choices)
    @app_commands.default_permissions(permissions=0)
    async def poke(interaction: discord.Interaction, scope: str, name: str, value: str):
        try:
            value = int(value)
        except ValueError:
            try:
                value = bool(strtobool(value))
            except ValueError:
                pass
        
        if type(value) != type(getattr(globals().get(scope), name)):
            await interaction.response.send_message(ephemeral=True, content=f"Type of new {value} value doesn't match the type of `{scope}.{name}`\'s value, get a grip man")

        setattr(globals().get(scope), name, value)
        await interaction.response.send_message(ephemeral=True, content=f"Done! `{scope}.{name}` = `{str(value)}`")

    @activity.error
    async def poke_error(interaction: discord.Interaction, error):
        if isinstance(error, discord.app_commands.errors.MissingPermissions):
            logging.info("[poke Command Error Handler] Invoke attempted by a peasant, but perms are missing lol")
            await interaction.response.send_message(ephemeral=True, content="You don't have the permission to do this")




    # Problem: this doesn't hide the command from permless people :(
    @commandTree.command(name="foo", description="foo", guild=None)
    @app_commands.checks.has_role("Editor")
    async def foo(interaction: discord.Interaction):
        await interaction.response.send_message(ephemeral=True, content="Bar")

    @activity.error
    async def foo_error(interaction: discord.Interaction, error):
        if isinstance(error, discord.app_commands.errors.MissingRole):
            logging.info("[foo Command Error Handler] Invoke attempted by a non-editor")
            await interaction.response.send_message(ephemeral=True, content="You don't have the permission to do this")




@tasks.loop(seconds=int(configPull("apiPollRate")))
async def listLobbies():
    statusMessage = composeStatus()
    if statusMessage != "nothingToDo" and firmStates.backendStatus == "online":
        logging.debug("[Holocorp Primary Loop] Got a new status message, posting...")
        try:
            await statusMessageHandler(firmStates.statusMessageText)
        except Exception as e:
            logging.warning(f"[Holocorp Primary Loop] Discord shitteth itself with {e} :(")




@client.event
async def on_ready():
    firmStates.channel = client.get_channel(int(configPull("statusMessageChannelID")))

    await commandTree.sync(guild=discord.Object(id=int(configPull("guildID"))))
    logging.info('Login successful (in as {0.user})'.format(client))
    volatileStates.hashAPILobby = "None"
    volatileStates.hashAPIPlayers = "None"
    logging.info("[onReady] Initializing the status message")
    if firmStates.backendStatus == "online" and listLobbies.is_running() == False:
        listLobbies.start()
    else:
        firmStates.statusMessageText = messageTemplate("standby")
        await statusMessageHandler(firmStates.statusMessageText)




@client.event
async def on_message(message):
    logging.debug("[onMessage] Triggered")

    if message.author.bot:
        logging.debug("[onMessage] Aborted, author is client")
        return

    if client.user in message.mentions and volatileStates.pingReplyType == "dumb":

        targetMessage = str(message.content).replace(f"<@{client.user.id}>", "").lstrip()

        if volatileStates.pingRepliesRigged:
            logging.debug(f"[onMessage] Replying with the rigged message of [{volatileStates.pingReplyRiggedMessage}] to {message.author}")

            await message.reply(volatileStates.pingReplyRiggedMessage.replace("!TARGETMESSAGE", targetMessage), mention_author=True)

            volatileStates.pingRepliesRigged = False
            volatileStates.pingReplyRiggedMessage = ""

            logging.debug("[onMessage] Reset rig parameters")

            return

        logging.debug(f"[onMessage] Replying to {message.author}")

        for attempts in range (16):
            replyCandidate = random.choice(volatileStates.pingReplies)
            if replyCandidate not in volatileStates.pingReplyCache: break
        if len(volatileStates.pingReplyCache) > 3: volatileStates.pingReplyCache = []

        await message.reply(replyCandidate.replace("!TARGETMESSAGE", targetMessage), mention_author=True)
    
    elif client.user in message.mentions and volatileStates.pingReplyType == "smart":
        async with message.channel.typing():
            logging.debug(f"[onMessage] Passing \"{message.content}\" to the LLM...")
            await message.reply(llmFetchResponse(str(message.content).replace(f"<@{client.user.id}>", "").lstrip(), message.author))
            return

client.run(tokenPull())