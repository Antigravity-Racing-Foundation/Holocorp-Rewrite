# This is the entry point for the bot. This file does the Discord API handling.
import discord
import datetime
import re
import logging
import sys
import os

from discord import app_commands
from discord.ext import commands
from discord.ext import tasks
from discord.ext.commands import MissingPermissions

from message_composer import *
from config_handler import *
from event_list_generate import generateEventList

from pathlib import Path

with open("./external/holocorp.workspace", "r+") as workspaceFile: # initialize workspace
    workspaceStart = f"hashAPILobby: HASH\nhashAPIPlayers: HASH\nbackendStatus: {configPull("defaultBackendStatus")}"
    workspaceFile.seek(0)

intents = discord.Intents.default()
intents.message_content = True

currentStatusAlreadyPosted = "None"
statusMessageCache = "None"
channel = "None"

class Client(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)

    async def setup_hook(self):
        await commandTree.sync()

client = Client(intents=discord.Intents.default()) # some discord api bullshit i pulled from past me's holocorp-classic

commandTree = app_commands.CommandTree(client) # command tree init (all my homies hate command trees)

logging.basicConfig(filename='holocorp.log', encoding='utf-8', level=logging.DEBUG)
logger = logging.getLogger("agrf_bot")
logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))




async def updateStatusMessage(desiredContent): # abstract of edit/send new message in status channel
    global statusMessageCache
    global channel

    if statusMessageCache == desiredContent:
        logging.debug["[updateStatusMessage] desiredContent matches cache, aborting!"]
        return("nothingToDo")
    logging.debug("[updateStatusMessage] Status message update routine started")
    existingMessageId = 0
    statusMessageCache = desiredContent

    async for previous_message in channel.history(limit=2):
        if previous_message.author == client.user:
            existingMessageId = previous_message.id
            logging.debug("[updateStatusMessage] existingMessageId defined!")

    if existingMessageId == 0:
        newMessage = await channel.send(desiredContent)
        existingMessageId = newMessage.id
        logging.info(f"[updateStatusMessage] Status message not found, new message ID: {str(existingMessageId)}")

    else:
        targetMessage = await channel.fetch_message(existingMessageId)
        await targetMessage.edit(content=desiredContent)
        logging.debug("[updateStatusMessage] Message updated!")




async def statusMessageHandler(statusMessage): # decide what to post to updateStatusMessage
    global currentStatusAlreadyPosted
    currentBackendStatus = workspacePull("status")
    if (currentBackendStatus == "offline" or currentBackendStatus == "maintenance") and currentStatusAlreadyPosted != "True":
        await updateStatusMessage(messageTemplate(currentBackendStatus))
        currentStatusAlreadyPosted = "True"
        if listLobbies.is_running() == True:
            listLobbies.stop()
            logging.debug("[statusMessageHandler] Stopped lobby listing")
    else:
        logging.debug("[statusMessageHandler] Invoking updateStatusMessage to post status...")
        await updateStatusMessage(statusMessage)




status_choices = [
    app_commands.Choice(name="online", value="online"),
    app_commands.Choice(name="offline", value="offline"),
    app_commands.Choice(name="maintenance", value="maintenance")
]
@commandTree.command(name="status", description="Change status message to `online`, `offline` or `maintenance` (clear_cache if status message stuck)", guild=None)
@app_commands.choices(status_command=status_choices)
@app_commands.default_permissions(permissions=0)
async def status(interaction: discord.Interaction, status_command: str): # set backend status command
    global currentStatusAlreadyPosted
    global statusMessageCache
    currentStatusAlreadyPosted = "False" # if this command is invoked, it will probably need to update the status message

    await interaction.response.send_message(ephemeral=True, content=f"Setting backend status to `{status_command.capitalize()}`")

    if status_command == "online" and listLobbies.is_running() == False:
        workspaceStore(status_command, "status")
        statusMessageCache = ""
        workspaceStore("HASH", "lobbies")
        workspaceStore("HASH", "players")
        listLobbies.start()
        logging.debug("[status] Started lobby listing routine and cleared cache")
    else:
        workspaceStore(status_command, "status")
        if listLobbies.is_running(): listLobbies.stop()
        await statusMessageHandler(messageTemplate(status_command))
        logging.debug("[status] Stopped lobby listing routine")

    logging.debug("[status] New backend status is now stored in the workspace")

@status.error
async def status_error(interaction: discord.Interaction, error):
    if isinstance(error, discord.app_commands.errors.MissingPermissions):
        logging.info("[status Command Error Handler] some cuck tried to change status without the perms lmao")
        await interaction.response.send_message(ephemeral=True, content="You don't have the permission to do this")




@commandTree.command(name="generate_events", description="Generate a weekly event list", guild=None)
@discord.app_commands.checks.has_permissions(manage_messages=True)
async def events(interaction: discord.Interaction):
    await interaction.response.send_message(ephemeral=True, content=f'here\'s your order, copyable and pastable!\n```{generateEventList()}```\n:3')

@events.error
async def events_error(interaction: discord.Interaction, error):
    if isinstance(error, discord.app_commands.errors.MissingPermissions):
        logging.info("[events Command Error Handler] some cuck tried to fuck with events without the perms lmao")
        await interaction.response.send_message(ephemeral=True, content="You don't have the permission to do this")
    else:
        raise(error)




activity_choices = [
    app_commands.Choice(name="playing", value="playing"),
    app_commands.Choice(name="watching", value="watching"),
    app_commands.Choice(name="clear", value="clear")
]
@commandTree.command(name="activity", description="Set bot activity to `Playing` or `Watching` with an arbitrary name or clear it", guild=None)
@app_commands.choices(activity_type=activity_choices)
@app_commands.describe(activity_name="Activity name (Playing _WipEout Fusion_ <-- this)")
@app_commands.default_permissions(permissions=0)
async def activity(interaction: discord.Interaction, activity_type: str, activity_name: str = None):
    if activity_type == "clear":
        await client.change_presence(activity=None)
        await interaction.response.send_message(ephemeral=True, content=f"Presence activity cleared (dropped activity_name you might've passed)")

    if activity_name == None:
        await interaction.response.send_message(ephemeral=True, content=f"Sooo what are we {activity_type}? (specify `activity_name` for non clear types dummy)")

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
        logging.info("[activity Command Error Handler] some cuck tried to change the activity without the perms lmao")
        await interaction.response.send_message(ephemeral=True, content="You don't have the permission to do this")




@tasks.loop(seconds=int(configPull("apiPollRate")))
async def listLobbies():
    statusMessage = composeStatus()
    if statusMessage != "nothingToDo" and workspacePull("status") == "online":
        logging.info("[Holocorp Primary Loop] Got a new status message, posting...")
        await statusMessageHandler(statusMessage)




@client.event
async def on_ready():
    global channel
    channel = client.get_channel(int(configPull("statusMessageChannelID")))

    await commandTree.sync(guild=discord.Object(id=int(configPull("guildID"))))
    logging.info('Login successful (in as {0.user})'.format(client))
    logging.info("[onReady] Initializing the status message")
    if workspacePull("status") == "online" and listLobbies.is_running() == False:
        listLobbies.start()
    else:
        statusMessageHandler("dummy")

client.run(tokenPull())