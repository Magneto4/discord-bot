import csv
import os

with open('test', 'w') as myfile:
    wr = csv.writer(myfile, quoting=csv.QUOTE_ALL)
    wr.writerow([])


def RegisteredServ(message):
    serv = message.guild.name
    for file in os.listdir():
        if file == (serv + ".csv"):
            return True
    return False
