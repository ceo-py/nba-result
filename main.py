import requests
from bs4 import BeautifulSoup
import re
import discord
from discord.ext import commands
import time
import urllib.request
import datetime

client = commands.Bot(command_prefix="!", help_command=None)
TOKEN = ("YOUR DISCORD BOT TOKEN HERE")
DISCORD_CHANNEL_NAME = "nba-result"
url_start = "https://sports.yahoo.com"


def getdata(url):
    r = requests.get(url)
    return r.text


@client.command()
async def nba(ctx):
    while True:
        today = datetime.date.today()
        previous_date = today - datetime.timedelta(days=1)
        link_game_name, odd_name, even_name, odd_score, even_score = list(), list(), list(), list(), list()
        htmldata = getdata(f"https://sports.yahoo.com/nba/scoreboard/?confId=&dateRange={previous_date}&schedState=")
        soup = BeautifulSoup(htmldata, 'html.parser')
        embed = discord.Embed(
            title=f"NBA Results {today}",
            colour=discord.Colour.blue())
        for nu, link_game in enumerate(soup.find_all('a', attrs={'href': re.compile("/nba/")})):
            if nu > 11:
                link_game_name.append(link_game.get('href'))
        for space, (name, score) in enumerate(zip(soup.find_all(class_="YahooSans Fw(700)! Fz(14px)!"),
                                                  soup.find_all(class_="YahooSans Fw(700)! Va(m) Fz(24px)!"))):
            if (space % 2) == 0:
                even_name.append(name.get_text())
                even_score.append(score.get_text())
            else:
                odd_name.append(name.get_text())
                odd_score.append(score.get_text())
        for name_o, score_o, name_e, score_e, game_url in zip(odd_name, odd_score, even_name, even_score,
                                                              link_game_name):
            html = urllib.request.urlopen(f"https://www.youtube.com/results?search_query={game_url}")
            video_ids = re.findall(r"watch\?v=(\S{11})", html.read().decode())
            game_highlight = f"https://www.youtube.com/watch?v={video_ids[0]}"
            if int(score_o) > int(score_e):
                score_show = f"**{name_o} : {score_o}**\n~~{name_e} : {score_e}~~"
            else:
                score_show = f"~~{name_o} : {score_o}~~\n**{name_e} : {score_e}**"
            embed.add_field(name=score_show,
                            value=f"[More Info]({url_start}{game_url})\n[Highlights]({game_highlight})",
                            inline=True)
        await ctx.send(embed=embed)
        time.sleep(86400)  # time in seconds when you want to give you the results again 86400 is 24 hours


client.run(TOKEN)
