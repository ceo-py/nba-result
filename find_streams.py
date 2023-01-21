from requests_html import HTMLSession
import json
import os
from dotenv import load_dotenv


load_dotenv()
session = HTMLSession()


def get_url(url: str) -> HTMLSession:
    return session.get(url).text


def generate_stream_data(url):
    file_html = get_url(url)
    start_index = file_html.find("props") - 2
    end_index = file_html.find("next-route-announcer") - 22
    return json.loads(file_html[start_index:end_index])["props"]["pageProps"]


def generate_game_address(data: dict) -> tuple:
    return data["metaTags"]["match_uuid"], data["metaTags"]["uuid"]


def find_game_links(url):
    data = generate_stream_data(url)
    match_uuid, uuid = generate_game_address(data)
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


def scrape_all_games(url):
    data = generate_stream_data(url)
    games_location = data["events"]
    try_next_games = 0
    result = {}
    for x in games_location:
        try:
            game_info = x["title"].split(" Live Stream -")[0]
            game_url = (
                f"{os.getenv('WEB_URL_FOR_GAME')}/{x['event_url']}/{x['match_uuid']}"
            )
            game_stream_urls = find_game_links(game_url)

            if game_stream_urls:
                result[game_info] = game_stream_urls
                try_next_games = 0
            else:
                try_next_games += 1
            if try_next_games == 3:
                break
        except:
            pass

    return result
