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
from lockjaw import *

class MyCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    #allows user to add their character to be tracked to database
    @slash.slash(
        name="add_character",
        description="add a character to be tracked",
        guild_ids=bot_guilds,
        options=[
            create_option(name="character", description="name of the character", option_type=3, required=True),
            create_option(name="tuppers", description="tuppers' names comma separated", option_type=3, required=True)
        ]
    )

    async def _add_character(ctx:SlashContext, character:str, tuppers:str):
        character_list = "data/characters/" + str(ctx.author_id) + "/character_list.csv"
        tupper_list = "data/characters/" + str(ctx.author_id) + "/tupper_list.csv"
        folder = "data/characters/" + str(ctx.author_id)
        if not(path.exists(folder)):
            if not(path.exists("data/characters/")):
                os.mkdir("data/characters/")
            os.mkdir(folder)
        tupper_array = []
        for tupper in tuppers.split(","):
            tupper_array += [[character, tupper]]
        print(tupper_array)
        data1 = pd.DataFrame([[character]])
        data2 = pd.DataFrame(tupper_array)
        if not(path.exists(character_list)) or not(path.exists(tupper_list)):
            data2.to_csv(tupper_list, index=False)
            data1.to_csv(character_list, index = False)
            await ctx.send("Done.")
        elif not(already_registered(ctx, character)):
            data1.to_csv(character_list, mode='a', index=False, header=False)
            data2.to_csv(tupper_list, mode='a', index=False, header=False)
            await ctx.send("Done.")
        else:
            await ctx.send("Character already registered.")

    #Remove character
    @slash.slash(
        name="remove_character",
        description="Remove character.",
        guild_ids=bot_guilds,
        options=[
            create_option(
                name="character",
                description="Name of the character you want to delete.",
                option_type=3,
                required=True
            )
        ]
    )

    async def _remove_character(ctx:SlashContext, character):
        character_list = "data/characters/" + str(ctx.author_id) + "/character_list.csv"
        tupper_list = "data/characters/" + str(ctx.author_id) + "/tupper_list.csv"
        if not(path.exists(tupper_list)) or not(path.exists(tupper_list)):
            await ctx.send(character + " doesn't exist.")
            return
        df1 = pd.read_csv(character_list)
        df2 = pd.read_csv(tupper_list)
        i = 0
        for row in df2.itertuples(index=False):
            if str(row[0]) == character:
                df2 = df2.drop(i)
                df2.to_csv(character_list, index=False)
            i += 1
        i = 0
        for row in df1.itertuples(index=False):
            if str(row[1]) == character:
                df1 = df1.drop(i)
                df1.to_csv(character_list, index=False)
                await ctx.send(character + " deleted.")
                return
            i += 1
        await ctx.send(character + " doesn't exist.")

    #Add tuppers to existing character
    @slash.slash(
        name="add_tupper",
        description="Add tupper to registered character.",
        guild_ids=bot_guilds,
        options=[
            create_option(name="character", description="Name of the character you want to edit.", option_type=3, required=True),
            create_option(name="tuppers", description="Tuppers you want to add comma separated.", option_type=3, required=True)
        ]
    )

    async def _add_tupper(ctx:SlashContext, character, tuppers):
        character_list = "data/characters/" + str(ctx.author_id) + "/character_list.csv"
        tupper_list = "data/characters/" + str(ctx.author_id) + "/tupper_list.csv"
        df1 = pd.read_csv(character_list)
        for row in df1.itertuples(index=False):
            if row[0] == character:
                tupper_array = []
                for tupper in tuppers.split(","):
                    if not(registered_tupper(ctx, character, tupper)):
                        tupper_array += [[character, tupper]]
                df2 = pd.DataFrame(tupper_array)
                df2.to_csv(tupper_list, mode='a', index=False, header=False)
                await ctx.send("Tuppers added to your tupper list.")
            return
        await ctx.send(character + " is not a registered character.")

    #Gives list of characters and associated tuppers
    @slash.slash(
        name="characters",
        description="Gives your character list",
        guild_ids=bot_guilds
    )

    async def _characters(ctx:SlashContext):
        character_list = "data/characters/" + str(ctx.author_id) + "/character_list.csv"
        tupper_list = "data/characters/" + str(ctx.author_id) + "/tupper_list.csv"
        if not(path.exists(character_list)):
            await ctx.send("You have no registered character.")
            return
        df = pd.read_csv(character_list)
        df2 = pd.read_csv(tupper_list)
        list = ""
        for row in df.itertuples(index=False):
            list += "**" + row[0] + "'s tuppers:**\n"
            for row2 in df2.itertuples(index=False):
                if row2[0] == row[0]:
                    list += "- " + row2[1] + "\n"
        if list == "":
            await ctx.send("You have no registered character.")
        else:
            await ctx.send(list)

    @slash.slash(
        name="remove_tupper",
        description="Add tupper to character.",
        guild_ids=bot_guilds,
        options=[
            create_option(name="character", description="Name of the character you want to edit.", option_type=3, required=True),
            create_option(name="tupper", description="Name of the tupper you want to add.", option_type=3, required=True)
        ]
    )

    async def _remove_tupper(ctx:SlashContext, character, tupper):
        tupper_list = "data/characters/" + str(ctx.author_id) + "/tupper_list.csv"
        if not(already_registered(character)):
            ctx.send(character + "isn't a registered character.")
        else:
            df = pd.read_csv(tupper_list)
            i = 0
            for row in df.itertuples(index=False):
                if row[0] == character and row[1] == tupper:
                    df.drop(i)
                    await ctx.send("Tupper name deleted.")
                    return
                i += 1
            await ctx.send(tupper + " isn't a registered tupper.")

def setup(bot):
    bot.add_cog(MyCog(bot))