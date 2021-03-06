import re
import discord
from discord.ext import commands
import time
import datetime
from requests_html import HTMLSession

client = commands.Bot(command_prefix="!", help_command=None)
TOKEN = ("Your TOKEN HERE!!!")
DISCORD_CHANNEL_NAME = "nba-result"
url_start = "https://sports.yahoo.com"
session = HTMLSession()


def getdata(url):
    r = session.get(url)
    return r


def get_all_info():
    nba_score_results = []
    today = datetime.date.today()
    previous_date = today - datetime.timedelta(days=1)
    htmldata = getdata(f"https://sports.yahoo.com/nba/scoreboard/?confId=&dateRange={previous_date}&schedState=")
    for game in range(1, 100):
        home_team = htmldata.html.xpath(
            f'//*[@id="scoreboard-group-2"]/div/div[2]/ul/li[{game}]/div/div[1]/a/div/div/div/div[2]/div/ul/li[1]/div[2]/div/span[1]',
            first=True)
        if home_team is None:
            break
        home_team_score = htmldata.html.xpath(
            f'//*[@id="scoreboard-group-2"]/div/div[2]/ul/li[{game}]/div/div[1]/a/div/div/div/div[2]/div/ul/li[1]/div[3]/span',
            first=True)
        away_team = htmldata.html.xpath(
            f'//*[@id="scoreboard-group-2"]/div/div[2]/ul/li[{game}]/div/div[1]/a/div/div/div/div[2]/div/ul/li[2]/div[2]/div/span[1]',
            first=True)
        away_team_score = htmldata.html.xpath(
            f'//*[@id="scoreboard-group-2"]/div/div[2]/ul/li[{game}]/div/div[1]/a/div/div/div/div[2]/div/ul/li[2]/div[3]/span[1]',
            first=True)
        game_url_you_tube = f"full+game+highlight{home_team.text}+{away_team.text}".replace(" ", "+")
        game_url_info = getdata(f"https://www.youtube.com/results?search_query={game_url_you_tube}")
        video_ids = re.findall(r"watch\?v=(\S{11})", game_url_info.text)
        game_highlight = f"https://www.youtube.com/watch?v={video_ids[1]}"
        nba_score_results.append(
            {"Home Team": home_team.text, "Home Team Score": int(home_team_score.text), "Away Team": away_team.text,
             "Away Team Score": int(away_team_score.text), "Game Highlight": game_highlight})
    return today, nba_score_results


@client.command()
async def nba(ctx):
    while True:
        today_, nba_score_results = get_all_info()
        embed = discord.Embed(
            title=f"NBA Results {today_}",
            colour=discord.Colour.blue()
        )
        for show in nba_score_results:
            stars, ends = "**", "~~"
            if show['Home Team Score'] < show['Away Team Score']:
                stars, ends = "~~", "**"
            embed.add_field(
                name=f"{stars}{show['Home Team']} : {show['Home Team Score']}{stars}\n{ends}{show['Away Team']} : "
                     f"{show['Away Team Score']}{ends}",
                value=f"[More Info]({url_start})\n[Highlights]({show['Game Highlight']})",
                inline=True)
        await ctx.send(embed=embed)
        del nba_score_results
        time.sleep(86400)


client.run(TOKEN)



## bs4 version
# import requests
# from bs4 import BeautifulSoup
# from datetime import date
# import re
# import discord
# from discord.ext import commands
# import time
# import urllib.request
# import datetime


# client = commands.Bot(command_prefix="!", help_command=None)
# TOKEN = ("your token here")
# DISCORD_CHANNEL_NAME = "nba-result" # discord channel to show results in
# url_start = "https://sports.yahoo.com"


# def getdata(url):
#     r = requests.get(url)
#     return r.text


# @client.command()
# async def nba(ctx):
#     while True:
#         today = datetime.date.today()
#         previous_date = today - datetime.timedelta(days=1)
#         name, score, space, nu, a = "", "", 0, 0, 0
#         odd_name = list()
#         even_name = list()
#         odd_score = list()
#         even_score = list()
#         htmldata = getdata(f"https://sports.yahoo.com/nba/scoreboard/?confId=&dateRange={previous_date}&schedState=")
#         soup = BeautifulSoup(htmldata, 'html.parser')
#         embed = discord.Embed(
#             title=f"NBA Results {today}",
#             colour=discord.Colour.blue()
#         )
#         for name, score in zip(soup.find_all(class_="YahooSans Fw(700)! Fz(14px)!"),
#                                soup.find_all(class_="YahooSans Fw(700)! Va(m) Fz(24px)!")):
#             space += 1
#             if (space % 2) == 0:
#                 even_name.append(name.get_text())
#                 even_score.append(score.get_text())
#                 a += 1
#             else:
#                 odd_name.append(name.get_text())
#                 odd_score.append(score.get_text())

#         for name_o, score_o, name_e, score_e in zip(odd_name, odd_score, even_name, even_score):
#             game_url = f"{name_o}+{name_e}".replace(" ", "+")
#             if int(score_o) > int(score_e):
#                 html = urllib.request.urlopen(f"https://www.youtube.com/results?search_query={game_url}")
#                 video_ids = re.findall(r"watch\?v=(\S{11})", html.read().decode())
#                 game_highlight = (f"https://www.youtube.com/watch?v={video_ids[0]}")
#                 embed.add_field(name=f"**{name_o} : {score_o}**\n~~{name_e} : {score_e}~~",
#                                 value=f"[More Info]({url_start})\n[Highlights]({game_highlight})",
#                                 inline=True)
#             else:
#                 html = urllib.request.urlopen(f"https://www.youtube.com/results?search_query={game_url}")
#                 video_ids = re.findall(r"watch\?v=(\S{11})", html.read().decode())
#                 game_highlight = (f"https://www.youtube.com/watch?v={video_ids[0]}")
#                 embed.add_field(name=f"~~{name_o} : {score_o}~~\n**{name_e} : {score_e}**",
#                                 value=f"[More Info]({url_start})\n[Highlights]({game_highlight})",
#                                 inline=True)

#         await ctx.send(embed=embed)
#         time.sleep(86400) # time in seconds -------------


# client.run(TOKEN)


