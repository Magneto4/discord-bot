from atexit import register
from cmath import nan
from doctest import DONT_ACCEPT_TRUE_FOR_1
from fileinput import filename
from genericpath import exists
from multiprocessing import context
from unicodedata import name
from venv import create
import numpy as np
import discord
import asyncio
import pandas as pd
import numpy as np
import csv
import os.path
import time
from os import path, mkdir
from discord.ext import commands
from discord import guild
from discord_slash import SlashCommand, SlashContext
from discord_slash.utils.manage_commands import create_choice, create_option

bot = commands.Bot(command_prefix="!")
slash = SlashCommand(bot, sync_commands=True)

@bot.event
async def on_ready():
    print("Ready")

bot_guilds = []
for guild in bot.guilds:
    bot_guilds += [guild.id]

del_author_id = None

bot.load_extension("tupper_management")

#what to do if bot is on an unregistered guild
def new_guild(guild):
    bot_guilds = []
    for guild in bot.guilds:
        bot_guilds += [guild.id]
    os.makedirs("data/" + str(guild.id))

def registered_tupper(ctx, character, tupper):
    tupper_list = "data/characters/" + str(ctx.author_id) + "/tupper_list.csv"
    df = pd.read_csv(tupper_list)
    for row in df.itertuples(index=False):
        if row[0] == character and row[1] == tupper:
            return(True)
    return(False)

#tells if character is already registered on file_name
def already_registered(ctx, character):
    character_list = "data/characters/" + str(ctx.author_id) + "/character_list.csv"
    df = pd.read_csv(character_list)
    for row in df.itertuples(index=False):
        print(row[0])
        if (row[0] == character):
            return (True)
    return (False)

def is_active_channel(channel, file_name):
    df = pd.read_csv(file_name)
    for row in df.itertuples(index=False):
        if (int(row[0]) == channel.id):
            return (True)
    return (False)

def is_started_thread_for_char(channel, file_name, user, character):
    df = pd.read_csv(file_name)
    for row in df.itertuples(index=False):
        if (int(row[0]) == channel.id) and (user.id == row[1]) and (character == row[2]) and int(row[5]) == 1:
            return (True)
    return (False)

def matching_line(df, ctx):
    i = 0
    for row in df.itertuples(index=False):
        if (int(row[0]) == ctx.channel_id):
            return (i)
        i += 1
    return (i)

#returns character associated with tupper, or none if the tupper isn't registered
def char_from_tupper(user, tupper, file_name):
    df = pd.read_csv(file_name)
    for row in df.itertuples(index=False):
        if int(row[0]) == user.id:
            i = 2
            while i < 12:
                if row[i] == tupper:
                    return (row[1])
                i += 1
    return (False)

def turns(message):
    file = "data/" + str(message.guild.id) + "/active_channels.csv"
    df = pd.read_csv(file)
    for row in df.itertuples(index=False):
        if int(row[0]) == message.channel.id and int(row[1]) == 1:
            return (True)
    return (False)

#from this point, we start writing the commands

@slash.slash(
    name="start",
    description="start a thread in the current channel",
    guild_ids=bot_guilds,
    options=[
        create_option(
            name="turns",
            description="specify if this thread doesn't have turns",
            option_type=3,
            required=False,
            choices=[
                create_choice(
                    name="Yes turns",
                    value="1"
                ),
                create_choice(
                    name="No turns",
                    value="0"
                ),
            ]
            )
        ],
)

async def _start(ctx:SlashContext, turns="1"):
    file_name = "data/" + str(ctx.guild.id) + "/active_channels.csv"
    if not(path.exists("data/" + str(ctx.guild.id) + "/")):
        os.mkdir("data/" + str(ctx.guild.id))
    if not(path.exists(file_name)):
        await ctx.send("Thread started!")
        df = pd.DataFrame([[ctx.channel.id, turns, ctx.channel.last_message_id]], columns = ["channel_id", "turns", "first_message"])
        df.to_csv(file_name, index=False)
    elif is_active_channel(ctx.channel, file_name):
        await ctx.send("This thread has already been started, or the previous one hasn't been ended.")
        return
    else:
        await ctx.send("Thread started!")
        df = pd.DataFrame([[ctx.channel.id, turns, ctx.channel.last_message_id]], columns = ["channel_id", "turns", "first_message"])
        df.to_csv(file_name, mode='a', index=False, header=False)
    

@slash.slash(
    name="end",
    description="End the thread in the current channel",
    guild_ids=bot_guilds
)
async def _end(ctx:SlashContext):
    channel_file = "data/" + str(ctx.guild.id) + "/active_channels.csv"
    thread_file = "data/" + str(ctx.guild.id) + "/threads.csv"
    if not(path.exists(channel_file)):
        await ctx.send("There is no active thread in this channel.")
        return
    if not(is_active_channel(ctx.channel, channel_file)):
        await ctx.send("There is no active thread in this channel.")     
        return
    df = pd.read_csv(channel_file)
    df = df.drop(matching_line(df, ctx))
    df.to_csv(channel_file, index=False)
    df = pd.read_csv(thread_file)
    i = 0
    for row in df.itertuples(index=False):
        if int(row[0]) == ctx.channel_id:
            df.at[i, "status"] = "0"
        i += 1
    df.to_csv(thread_file, index=False)
    await ctx.send("Thread ended.")

def give_character_threads(character, ctx):
    thread_file = "data/" + str(ctx.guild.id) + "/threads.csv"
    list = "**" + character + "'s threads:**\n"
    df = pd.read_csv(thread_file)
    for row in df.itertuples(index=False):
        if row[1] == ctx.author.id and row[2] == character and int(row[5]) == 1:
            if int(row[3]) == 0:
                sign = ":red_circle:"
            if int(row[3]) == 1:
                sign = ":green_circle:"
            if int(row[3]) == 2:
                sign = ":orange_circle:"
            list += sign + " " + bot.get_channel(row[0]).mention + "\n"
    return (list)

def give_character_ended_threads(character, ctx):
    thread_file = "data/" + str(ctx.guild.id) + "/threads.csv"
    list = "**" + character + "'s ended threads:**\n"
    df = pd.read_csv(thread_file)
    for row in df.itertuples(index=False):
        if row[1] == ctx.author.id and row[2] == character and int(row[5]) == 0:
            list += "https://discordapp.com/channels/" + str(ctx.guild_id) + "/" + str(row[0]) + "/" + str(row[4]) + "\n"
    return (list)

@slash.slash(
    name="archive",
    description="Give you the list of your ended threads on the current server.",
    guild_ids=bot_guilds,
    options=[
        create_option(
            name="character",
            description="name of the character who's threads you want to see.",
            option_type=3,
            required=False
        )
    ]
)

async def _archive(ctx:SlashContext, character = False):
    character_list = "data/characters/" + str(ctx.author_id) + "/character_list.csv"
    thread_file = "data/" + str(ctx.guild.id) + "/threads.csv"
    if not(path.exists(thread_file)):
        await ctx.send("No threads have been started on this server.")
        return
    if not(path.exists(character_list)):
        if character:
            await ctx.send(character + " isn't registered. Please use /add_character to add them.")
        else:
            await ctx.send("You have no registered characters. Please use /add_character to add one.")
        return
    if character:
        if not(already_registered(ctx, character)):
            await ctx.send(character + " isn't registered. Please use /add_character to add them.")
        else:
            await ctx.send(give_character_ended_threads(character, ctx))
        return
    df = pd.read_csv(character_list)
    reply = ""
    for row in df.itertuples(index=False):
        reply += give_character_ended_threads(row[1], ctx)
    if reply == "":
        await ctx.send("You have no registered characters. Please use /add_character to add one.")
    else:
        await ctx.send(reply)

@slash.slash(
    name="active_threads",
    description="Gives you the list of your active threads on the current server.",
    guild_ids=bot_guilds,
    options=[
        create_option(
            name="character",
            description="Name of the character who's threads you want to see.",
            option_type=3,
            required=False
        )
    ]
)

async def _active_threads(ctx:SlashContext, character = False):
    character_list = "data/characters/" + str(ctx.author_id) + "/character_list.csv"
    thread_file = "data/" + str(ctx.guild.id) + "/threads.csv"
    channel_file = "data/" + str(ctx.guild.id) + "/active_channels.csv"
    if not(path.exists(thread_file)) or not(path.exists(channel_file)):
        await ctx.send("No threads have been started on this server.")
        return
    if not(path.exists(character_list)):
        if character:
            await ctx.send(character + " isn't registered. Please use /add_character to add them.")
        else:
            await ctx.send("You have no registered characters. Please use /add_character to add one.")
        return
    if character:
        if not(already_registered(ctx, character)):
            await ctx.send(character + " isn't registered. Please use /add_character to add them.")
        else:
            await ctx.send(give_character_threads(character, ctx))
        return
    df = pd.read_csv(character_list)
    reply = ""
    for row in df.itertuples(index=False):
        reply += give_character_threads(row[0], ctx)
    if reply == "":
        await ctx.send("You have no registered characters. Please use /add_character to add one.")
    else:
        await ctx.send(reply)

#Various bot events

#adds guild when joining it
@bot.event
async def on_guild_join(guild):
    new_guild(guild)

def change_turns(thread_file, character, channel):
    df = pd.read_csv(thread_file)
    i = 0
    for row in df.itertuples(index=False):
        if int(row[0]) == channel.id and int(row[5]) == 1:
            if row[2] == character:
                df.at[i, "turn"] = "0"
            else:
                df.at[i, "turn"] = "1"
        i += 1
    df.to_csv(thread_file, index=False)

def get_first_message(channel, thread_file): 
    df = pd.read_csv(thread_file)
    for row in df.itertuples(index=False):
        if int(row[0]) == channel.id:
            return (row[2])

@bot.event
async def on_message_delete(message):
    if not(tupper):
        return
    thread_file = "data/" + str(message.guild.id) + "/threads.csv"
    character_file = "data/characters.csv"
    channel_file = "data/" + str(message.guild.id) + "/active_channels.csv"
    if not(path.exists(character_file)):
        return
    character = char_from_tupper(message.author, tup_name, character_file)
    if not(character):
        return
    first_message = get_first_message(message.channel, channel_file)
    new_line = pd.DataFrame([[message.channel.id, message.author.id, character, 0, first_message, 1]], columns=["channel_id", "user_id", "character", "turn", "first_message", "status"])
    if not(path.exists(thread_file)):
        if character != None:
            new_line.to_csv(thread_file, index=False)
        return
    if turns(message):
        change_turns(thread_file, character, message.channel)
    if not(is_started_thread_for_char(message.channel, thread_file, message.author, character)):
        new_line.to_csv(thread_file, mode='a', index=False, header=False)

@bot.event
async def on_message(message):
    global tupper
    global tup_name
    if not(message.author.bot):
        tupper = False
        return
    try:
        webhook = await bot.fetch_webhook(message.webhook_id)
    except discord.errors.NotFound:
        tupper = False
        return
    if not(webhook.name == "Tupperhook"):
        tupper = False
        return
    file_name = "data/" + str(message.guild.id) + "/active_channels.csv"
    if not(path.exists(file_name)):
        tupper = False
        return
    if not(is_active_channel(message.channel, file_name)):
        tupper = False
        return
    tupper = True
    tup_name = message.author.name

bot.run("ODYzODE0ODkwMzU1Mjk0MjMw.YOsYTg.tie3LeaHc_mArggvEsHGhF8iBno") #token not active