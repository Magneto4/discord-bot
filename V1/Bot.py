from codecs import register
from re import X
import discord
import asyncio
import csv
import os
import time
from discord import message
from discord.enums import DefaultAvatar
from discord.ext import commands
from discord.flags import MessageFlags


client = discord.Client()

def Bool(str):
    return str == "True"

print("test")

@client.event
async def on_ready():
    print("Le bot est prêt !")

#Convert csv file to python array
def ArrayFromCsv(file):
    data = []
    with open(file, newline='') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            data.append(row)
    return data

def DataImport():
    servlist = []
    with open("servlist.csv") as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            servlist = row
    servdata = []
    for serv in servlist:
        data = ArrayFromCsv(serv + ".csv")
        servdata.append(data)
    return (servlist, servdata)

#Return True if character already registered in server, else return False
def RegisteredChar(char, serv, servdata, servlist):
    servnumber = ServNumber(serv, servlist)
    for thread in servdata[servnumber]:
        if thread[0] == char:
            return True
    return False

#Return True if guild already registered, else False
def RegisteredServer(serv, servlist):
    for i in servlist:
        if i == serv:
            return True
    return False

#Replies true if thread is already registered
def RegisteredThread(message, servdata, servlist):
    def RegisteredAuthor(l, n):
        if l == []:
            return "no"
        for name in l:
            if name == n:
                return "yes"
        return "partially"
    servnumber = ServNumber(message.guild.name, servlist)
    l = []
    for thread in servdata[servnumber]:
            if len(thread) > 1:
                if thread[1] == str(message.channel.id) and thread[4]:
                    l += [thread[0]]
    return RegisteredAuthor(l, message.author.name)

#Change turn for thread from which the message comes from
def ChangeTurns(message, servdata, servlist):
    i = 0
    serv = message.guild.name
    servnumber = ServNumber(serv, servlist)
    chanid = message.channel.id
    for thread in servdata[servnumber]:
        if len(thread) > 1:
            if thread[1] == str(chanid) and thread[4]:
                if thread[3] == "Your":
                    servdata[servnumber][i][3] = "Their"
                else:
                    servdata[servnumber][i][3] = "Your"
        i += 1
    return servdata

#Creates thread for message
def AddThread(message, servdata, servlist):
    servnumber = ServNumber(message.guild.name, servlist)
    servdata[servnumber].append([message.author.name, message.channel.id , message.jump_url , "Their" , True])
    return servdata

def ServNumber(serv, servlist):
    j = 0
    for i in servlist:
        if serv == i:
            return j
        j += 1

def BackUpServ(servdata, servlist):
    i = 0
    for serv in servdata:
        servname = servlist[i]
        with open(servname + '.csv', 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(serv)
        i += 1
    with open("servlist.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(servlist)

def CharsActiveThreads(char, servnumber, servdata):
    threads = []
    for thread in servdata[servnumber]:
        if len(thread) > 1:
            if thread[0] == char and Bool(thread[4]):
                threads += [thread]
    return threads

async def MessageFromLink(link):
    linklist = link.split('/')
    channel_id = int(link[6])
    msg_id = int(link[5])
    server_id = int(link[4])
    server = client.get_guild(server_id)
    channel = server.get_channel(channel_id)
    message = await channel.fetch_message(msg_id)
    return message

@client.event
async def on_message(message):
    servlist, servdata = DataImport()
    content = message.content
    serv = message.guild.name
    chanid = message.channel.id
    if content.startswith("!tracker "):
        servnumber = ServNumber(serv, servlist)
        char = content.replace("!tracker ", "")
        #Creates array for the server if there isn't one already
        if not(RegisteredServer(serv, servlist)):
            servdata = servdata + [[["character name" , "channel id" , "first message url" , "turn" , "active"]]]
            servlist = servlist + [serv]
        #Add character to file
        servnumber = ServNumber(serv, servlist)
        if not(RegisteredChar(char, serv, servdata, servlist)):
            servdata[servnumber] = servdata[servnumber] + [[char]]
        threads = CharsActiveThreads(char, servnumber, servdata)
        reply = "**" + char + " thread tracker**" + "\n"
        for thread in threads:
            channel = discord.utils.get(message.guild.text_channels, id=thread[1])
            reply += channel.mention + ", " + thread[3] + " turn" + "\n"
        await message.channel.send(reply)
        await message.delete()
        tracker = message.channel.last_message.jump_url
        servdata[servnumber] += [[char, tracker]]
    elif content.startswith("!end"):
        servnumber = ServNumber(serv, servlist)
        i = 0
        for thread in servdata[servnumber]:
            if len(thread) > 1:
                if str(chanid) == thread[1] and Bool(thread[4]):
                    servdata[servnumber][i][4] = "False"
            i += 1
        await message.add_reaction('\N{THUMBS UP SIGN}')
    elif content.startswith("!delete"):
        servnumber = ServNumber(serv, servlist)
        channel_id = message.channel_mentions[0].id
        i = 0
        l= []
        for thread in servdata[servnumber]:
            if len(thread) > 1:
                if thread[1] == str(channel_id) and Bool(thread[4]):
                    l += [i]
            i += 1
        for i in l[::-1]:
            del servdata[servnumber][i]
        await message.add_reaction('\N{THUMBS UP SIGN}')
    # if content.startswith("!register ")
    #     thread = content.replace("!register archive ", "")
    else:
        if message.author.bot:
            servnumber = ServNumber(serv, servlist)
            name = message.author.name
            if RegisteredChar(name, serv, servdata, servlist):
                registered = RegisteredThread(message, servdata, servlist)
                if registered == "yes":
                    servdata = ChangeTurns(message, servdata, servlist)
                elif registered == "partially":
                    servdata = ChangeTurns(message, servdata, servlist)
                    servdata = AddThread(message, servdata, servlist)
                else:
                    servdata = AddThread(message, servdata, servlist)
            for thread in servdata[servnumber]:
                if len(thread) == 2:
                    for thread in threads:
                        char = thread[0]
                        reply = "**" + char + " thread tracker**" + "\n"
                        reply += channel.mention + ", " + thread[3] + " turn" + "\n"
                    tracker = MessageFromLink(thread[1])
                    tracker.edit(reply)
    BackUpServ(servdata, servlist)

client.run("ODYzODE0ODkwMzU1Mjk0MjMw.YOsYTg.tie3LeaHc_mArggvEsHGhF8iBno")