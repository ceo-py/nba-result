import datetime
import discord
import os
import re

from discord.ext import commands, tasks
from dotenv import load_dotenv
from requests_html import HTMLSession

client = commands.Bot(command_prefix="?", help_command=None, intents=discord.Intents.all())
DISCORD_CHANNEL_NAME = "nba-result"
TEAM_URL = 'https://www.nba.com/'
session = HTMLSession()
load_dotenv()


def getdata(url: str) -> object:
    r = session.get(url)
    return r


def get_current_date() -> str:
    return datetime.date.today()


def get_previous_date(current_date: str):
    return current_date - datetime.timedelta(days=1)


def get_url() -> str:
    return f"https://www.nba.com/games?date={get_previous_date(get_current_date())}"


async def find_emojis(ctx: object, team_name: str) -> str:
    for team in ctx.guild.emojis:
        if team_name in team.name:
            return str(team)


def find_data_from(url: str) -> tuple:
    html_decode = url
    games_leaders = html_decode.html.find(".GameCard_gcLeaders__Yn1ru")
    games_information = html_decode.html.find(".GameCard_gcMain__q1lUW")
    return games_information, games_leaders


def generate_link(link_name: str, url: str) -> str:
    return f"[{link_name}]({url})"


async def find_youtube_video_link(home_team: str, away_team: str, previous_date: str) -> str:
    game_url_you_tube = f"show+video+from+hooper+full+game+highlights+{home_team}+{away_team}+{previous_date}".replace(
        " ", "+")
    game_url_info = getdata(f"https://www.youtube.com/results?search_query={game_url_you_tube}")
    video_ids = re.findall(r"watch\?v=(\S{11})", game_url_info.text)
    return f"https://www.youtube.com/watch?v={video_ids[1]}"


async def generate_result() -> list:
    result = []
    for games, players in zip(*find_data_from(getdata(get_url()))):
        home_team_name, home_team_record, home_team_score, type_result, away_team_score, away_team_name, away_team_record, *__ = games.text.split(
            "\n")
        players = players.text.split("\n")

        home_team_player_name, home_team_player_information, home_team_player_pts, home_team_player_reb, home_team_player_ast, \
        away_team_player_name, away_team_player_information, away_team_player_pts, away_team_player_reb, away_team_player_ast, \
            = players[4:] if len(players) != 15 else players[4:-1]

        result.append(
            {f"Home": {
                "Team": {"name": away_team_name.split()[-1], "record": away_team_record, "score": int(away_team_score)},
                "Player": {"name": away_team_player_name, "information": away_team_player_information,
                           "pts": away_team_player_pts, "reb": away_team_player_reb,
                           "ast": away_team_player_ast}},
                f"Away": {"Team": {"name": home_team_name.split()[-1], "record": home_team_record,
                                   "score": int(home_team_score)},
                          "Player": {"name": home_team_player_name, "information": home_team_player_information,
                                     "pts": home_team_player_pts, "reb": home_team_player_reb,
                                     "ast": home_team_player_ast}},
                "Highlights": await find_youtube_video_link(home_team_name, away_team_name,
                                                            get_previous_date(get_current_date()))})
    return result


async def show_result(ctx) -> None:
    today_, nba_score_results = get_current_date(), await generate_result()
    embed = discord.Embed(
        title=f"NBA Results for {today_}",
        colour=discord.Colour.blue(),
    )
    embed.set_thumbnail(url='https://cdn.discordapp.com/attachments/983670671647313930/1057801162142777454/NBA.png')
    for show in nba_score_results:
        stars, ends = "**", "__"
        if show['Home']['Team']['score'] < show['Away']['Team']['score']:
            stars, ends = "__", "**"
        embed.add_field(
            name=f"{await find_emojis(ctx, show['Away']['Team']['name'])} "
                 f"({show['Away']['Team']['record']}) "
                 f"{stars}{show['Away']['Team']['name'].upper()}{stars} {show['Away']['Team']['score']} @ "
                 f"{show['Home']['Team']['score']} "
                 f"{ends}{show['Home']['Team']['name'].upper()}{ends}"
                 f" ({show['Home']['Team']['record']}) "
                 f"{await find_emojis(ctx, show['Home']['Team']['name'])} ",
            value=f"{generate_link(show['Away']['Player']['name'], TEAM_URL + show['Away']['Team']['name'])} "
                  f"{show['Away']['Player']['pts']}/{show['Away']['Player']['reb']}/{show['Away']['Player']['ast']}\n"
                  f"{generate_link(show['Home']['Player']['name'], TEAM_URL + show['Home']['Team']['name'])} "
                  f"{show['Home']['Player']['pts']}/{show['Away']['Player']['reb']}/{show['Home']['Player']['ast']}"
                  f"\n{generate_link('Highlights', show['Highlights'])}",
            inline=False)
    await ctx.send(embed=embed)


@tasks.loop(seconds=0)
async def task_loop(ctx):
    await show_result(ctx)


@client.command()
async def nba_start(ctx, time_value):
    task_loop.change_interval(hours=float(time_value))
    await ctx.send(f"```It's set on every {time_value}h to show the results!```")
    task_loop.start(ctx)


@client.command()
async def nba_stop(ctx):
    await ctx.send(f"```It's canceled!```")
    task_loop.cancel()


client.run(os.getenv("TOKEN"))
