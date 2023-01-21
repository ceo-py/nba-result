import datetime
import discord
import re

from discord.ext import commands, tasks
from find_streams import scrape_all_games, HTMLSession, os


client = commands.Bot(
    command_prefix="!", help_command=None, intents=discord.Intents.all()
)
TEAM_URL = "https://www.nba.com/"
VIDEO_CHANNELS = ("CCBN", "Hooper", "The Asylum", "FreeDawkins")
session = HTMLSession()


def getdata(url: str) -> session:
    r = session.get(url)
    return r


def get_current_date() -> str:
    return datetime.date.today()


def get_previous_date(current_date: str):
    return current_date - datetime.timedelta(days=1)



def convert_data_time(data_to_convert: datetime) -> str:
    return (
        f"{data_to_convert.strftime('%b')}+{data_to_convert.day}+{data_to_convert.year}"
    )


def get_url() -> str:
    return f"https://www.nba.com/games?date={get_previous_date(get_current_date())}"


async def find_emojis(ctx: client, team_name: str) -> str:
    for team in ctx.guild.emojis:
        if team_name in team.name:
            return str(team)


def generate_player_output(player_data: str, team_name: str) -> str:
    data = player_data.split("\n")
    player_link = generate_link(data[0], TEAM_URL + team_name)
    return f"{player_link} {data[-3]}/{data[-2]}/{data[-1]}"


def find_data_from(url: session) -> tuple:
    classes_to_look_for = (
        ".MatchupCardScore_p__dfNvc",
        ".MatchupCardTeamName_teamName__9YaBA",
        ".MatchupCardTeamRecord_record__20YHe",
        ".GameCardLeaders_gclRow__VMSee",
    )
    return (url.html.find(f"{x}") for x in classes_to_look_for)


def generate_link(link_name: str, url: str) -> str:
    return f"[{link_name}]({url})"


async def find_youtube_video_link(
    home_team: str, away_team: str, previous_date: str
) -> tuple:

    find_videos = []
    for channel in VIDEO_CHANNELS:
        game_url_you_tube = f"{channel}+Highlights+full+game+{home_team}+vs+{away_team}+{convert_data_time(previous_date)}".replace(
            " ", "+"
        )
        game_url_info = getdata(
            f"https://www.youtube.com/results?search_query={game_url_you_tube}&sp=EgYIAhABGAM%253D"
        )
        find_videos += re.findall(r"watch\?v=(\S{11})", game_url_info.text)
    return (f"https://www.youtube.com/watch?v={x}" for x in find_videos[:5])


def get_all_channels_id(client: client) -> tuple:
    return (
        channel.id
        for server in client.guilds
        for channel in server.channels
        if channel.name == os.getenv("DISCORD_CHANNEL_NAME")
    )


def get_nba_team_names(data: str) -> tuple:
    return [x.split()[-1] for x in data.split(" vs ")]


async def generate_result() -> list:
    result = []
    team_scores, team_names, team_records, player_stats = find_data_from(
        getdata(get_url())
    )
    for i in range(0, len(team_scores), 2):
        away_team_name = team_names[i].text.split()[-1]
        home_team_name = team_names[i + 1].text.split()[-1]
        away_team_record = team_records[i].text
        home_team_record = team_records[i + 1].text
        away_team_score = team_scores[i].text
        home_team_score = team_scores[i + 1].text
        away_team_player_name = generate_player_output(
            player_stats[i].text, away_team_name
        )
        home_team_player_name = generate_player_output(
            player_stats[i + 1].text, home_team_name
        )

        result.append(
            {
                f"Away": {
                    "Team": {
                        "name": away_team_name,
                        "record": away_team_record,
                        "score": int(away_team_score),
                    },
                    "Player": {"name": away_team_player_name},
                },
                f"Home": {
                    "Team": {
                        "name": home_team_name,
                        "record": home_team_record,
                        "score": int(home_team_score),
                    },
                    "Player": {"name": home_team_player_name},
                },
                "Highlights": await find_youtube_video_link(
                    home_team_name,
                    away_team_name,
                    get_previous_date(get_current_date()),
                ),
            }
        )

    return result


async def show_result(ctx: client) -> discord.Embed:
    today_, nba_score_results = (
        get_current_date(),
        await generate_result(),
    )
    embed = discord.Embed(
        title=f"NBA Results for {today_}",
        colour=discord.Colour.blue(),
    )
    embed.set_thumbnail(
        url="https://cdn.discordapp.com/attachments/983670671647313930/1057801162142777454/NBA.png"
    )
    for show in nba_score_results:
        home_sing, away_sing = (
            ("", await find_emojis(ctx, '9410pinkarrowL'))
            if show["Home"]["Team"]["score"] > show["Away"]["Team"]["score"]
            else (await find_emojis(ctx, '9410pinkarrowR'), "")
        )

        embed.add_field(
            name=f"{await find_emojis(ctx, show['Away']['Team']['name'])} "
            f"({show['Away']['Team']['record']}) "
            f"{show['Away']['Team']['name'].upper()}{home_sing} {show['Away']['Team']['score']} @ "
            f"{show['Home']['Team']['score']} "
            f"{away_sing}{show['Home']['Team']['name'].upper()}"
            f" ({show['Home']['Team']['record']}) "
            f"{await find_emojis(ctx, show['Home']['Team']['name'])} ",
            value=f"**Game Leaders**\n{show['Away']['Player']['name']}\n"
            f"{show['Home']['Player']['name']}\n"
            f"{await find_emojis(ctx, 'youtube')} **Highlights** {', '.join(generate_link(f'Link {pos}', link) for pos, link in enumerate(show['Highlights'], 1))}",
            inline=False,
        )
    return embed


@tasks.loop(seconds=0)
async def task_loop() -> None:
    embed_result = await show_result(client.get_channel(917894815016955965))
    for id_channel in get_all_channels_id(client):
        ctx = client.get_channel(id_channel)
        await ctx.send(embed=embed_result)


@client.command()
async def nba_start(ctx: client, time_value: float) -> None:
    if str(ctx.author) == os.getenv("OWNER"):
        task_loop.change_interval(hours=float(time_value))
        if task_loop.next_iteration:
            task_loop.cancel()
        await ctx.send(
            f"```It's set on every {int(time_value)}h to show the results!```"
        )
        task_loop.start()


@client.command()
async def live(ctx: client) -> None:
    live_games = scrape_all_games(os.getenv('NBA'))

    embed = discord.Embed(
        title=f"NBA Live Games",
        colour=discord.Colour.blue(),
    )
    embed.set_thumbnail(
        url="https://cdn.discordapp.com/attachments/983670671647313930/1066494679866146866/live.gif"
    )

    for k, v in live_games.items():
        away_team, home_team = get_nba_team_names(k)
        links = []
        for pos, link in enumerate(v, 1):
            gen_link = generate_link(f"Link {pos}", link)
            if len(gen_link) + sum(len(x) for x in links) > 1000:
                break
            links.append(gen_link)
        embed.add_field(
            name=f"{await find_emojis(ctx, away_team)} **{k}** {await find_emojis(ctx, home_team)}",
            value=f"{await find_emojis(ctx, '3716_ArrowRightGlow')} {', '.join(links)}",
            inline=False,
        )

    await ctx.send(embed=embed)


client.run(os.getenv("TOKEN"))
