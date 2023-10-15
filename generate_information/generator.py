import date.date_manipulations as date
import re
import json
import os

from dotenv import load_dotenv
from requests_html import HTMLSession


load_dotenv()
asession = HTMLSession()


async def generate_url() -> str:
    return f"{os.getenv('START_URL_GAMES')}{await date.get_current_date()}"


async def generate_youtube_video_link(
    home_team: str, away_team: str, previous_date: str
) -> tuple:
    result = set()
    find_videos = []
    for channel in os.getenv("VIDEO_CHANNELS").split(", "):
        # game_url_you_tube = f"{channel}+Highlights+full+game+{home_team}+vs+{away_team}+{await date.get_current_date()}".replace(
        #     " ", "+"
        # )
        game_url_you_tube = f"{channel}+Highlights+full+game+{home_team}+vs+{away_team}".replace(
            " ", "+"
        )
        # game_url_info = get_url(
        #     f"{os.getenv('YOUTUBE_SEARCH_LINK')}{game_url_you_tube}{os.getenv('CRITERIA')}"
        # )
        game_url_info = get_url(
            f"{os.getenv('YOUTUBE_SEARCH_LINK')}{game_url_you_tube}{os.getenv('CRITERIA')}"
        )
        find_videos += re.findall(r"watch\?v=(\S{11})", game_url_info.text)

    for x in find_videos:
        result.add(x)
        if len(result) == 5:
            break
    return (f"{os.getenv('YOUTUBE_VIDEO_LINK')}{x}" for x in result)


# async def generate_players_information(data: dict) -> map:
#     return (
#         f"{x['teamTricode']}/ {x['position']}/ {x['name']}: {x['points']}/ {x['rebounds']}/ {x['assists']}"
#         for x in data.values()
#     )

async def generate_players_information(data: dict) -> map:
    return (
        f"{x['teamTricode']}/ {x['position']}/ {x['name']}: {x['points']}/ {x['rebounds']}/ {x['assists']}"
        for x in data
    )


async def generate_team_names(data: dict) -> str:
    return f"{data['wins']}-{data['losses']}", data["teamName"], int(data["score"])


async def generate_player_output(player_data: str, team_name: str) -> str:
    data = player_data.split(": ")
    player_link = await generate_link(
        data[0].split("/ ")[-1], os.getenv("TEAM_URL") + team_name
    )
    return f"{'/ '.join(data[0].split('/ ')[:-1])} {player_link} {data[1]}"


async def generate_result() -> list:
    result = []
    # data = json.loads(get_url(await generate_url()).html.find("#__NEXT_DATA__")[0].text)
    data = json.loads(get_url(await generate_url()).html.find("#__NEXT_DATA__")[0].text)

    try:
        # all_game_results = data["props"]["pageProps"]["games"]
        all_game_results = data['props']['pageProps']['gameCardFeed']['modules'][0]['cards']
    except KeyError:
        return

    for item in all_game_results:
        home_team_data, away_team_data = item['cardData']['homeTeam'], item['cardData']['awayTeam']
        # (
        #     home_team_player_name,
        #     away_team_player_name,
        # ) = await generate_players_information(item["gameLeaders"])
        (
            home_team_player_name,
            away_team_player_name,
        ) = await generate_players_information((home_team_data['teamLeader'], away_team_data['teamLeader']))

        # home_team_record, home_team_name, home_team_score = await generate_team_names(
        #     item["homeTeam"]
        # )
        # away_team_record, away_team_name, away_team_score = await generate_team_names(
        #     item["awayTeam"]
        # )


        home_team_record, home_team_name, home_team_score = await generate_team_names(
            home_team_data
        )
        away_team_record, away_team_name, away_team_score = await generate_team_names(
            away_team_data
        )

        away_team_player_name = await generate_player_output(
            away_team_player_name, away_team_name.split()[-1]
        )
        home_team_player_name = await generate_player_output(
            home_team_player_name, home_team_name.split()[-1]
        )
        highlights = tuple(
            await generate_youtube_video_link(
                home_team_name,
                away_team_name,
                await date.get_current_date(),
            )
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
                "Highlights": highlights,
            }
        )

    return result


def get_url(url: str) -> HTMLSession:
    return asession.get(url)


async def get_nba_team_names(data: str) -> tuple:
    return [x.split()[-1] for x in data.split(" vs ")]


async def generate_stream_data(url) -> dict:
    file_html = get_url(url).text
    start_index = file_html.find(os.getenv("HTML_START_IND")) - 2
    end_index = file_html.find(os.getenv("HTML_END_IND")) - 22
    return json.loads(file_html[start_index:end_index])[os.getenv("HTML_START_IND")][
        os.getenv("HTML_END")
    ]


async def generate_game_address(data: dict) -> tuple:
    return (
        data[os.getenv("URL_TAG_START")][os.getenv("URL_MATCH_ID")],
        data[os.getenv("URL_TAG_START")][os.getenv("URL_ID")],
    )


async def generate_link(link_name: str, url: str) -> str:
    return f"[{link_name}]({url})"


async def generate_link_correct_len(data: list) -> list:
    links = []
    for pos, link in enumerate(data, 1):
        gen_link = await generate_link(f"Link {pos}", link)

        if len(gen_link) + sum(len(x) for x in links) > 1000:
            break

        links.append(gen_link)

    return links


async def find_game_links(url) -> list:
    data = await generate_stream_data(url)
    match_uuid, uuid = await generate_game_address(data)
    result = []
    for collection in data["streams"][1:]:
        for value in collection.values():
            if value:
                for y in value.values():
                    if y:
                        for x in y:
                            if x:
                                stream = x["stream"]
                                if "iframe" not in stream:
                                    result.append(stream)
                                else:
                                    result.append(
                                        f"{os.getenv('STREAM_URL')}/{match_uuid}/{uuid}/{x['uuid']}"
                                    )

    return result


async def scrape_all_games(url: HTMLSession) -> dict:
    data = await generate_stream_data(url)
    games_location = data["events"]
    try_next_games = 0
    result = {}
    for x in games_location:
        try:
            game_info = x["title"].split(" Live Stream -")[0]
            game_url = (
                f"{os.getenv('WEB_URL_FOR_GAME')}/{x['event_url']}/{x['match_uuid']}"
            )
            game_stream_urls = await find_game_links(game_url)

            if game_stream_urls:
                result[game_info] = game_stream_urls
                try_next_games = 0
            else:
                try_next_games += 1
            if try_next_games == 2:
                break
        except KeyError:
            pass

    return result


def find_specific_game_all_sports(url: HTMLSession):
    ...
