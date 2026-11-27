"""Self-check for generate_result() edge cases. No network, no pytest needed.

Run from the repo root: venv/bin/python test_generate_result.py
"""
import asyncio
import json
import sys
import time
import types

sys.path.insert(0, ".")

# Stub requests_html so this check runs without the real dependency installed.
fake = types.ModuleType("requests_html")
fake.HTMLSession = lambda: types.SimpleNamespace(get=lambda url, **kw: None)
sys.modules["requests_html"] = fake

from generate_information import generator

# Keep the real get_url around: the cases below swap it out for a fake.
real_get_url = generator.get_url


def fake_response(payload):
    """Shape like requests_html: response.html.find(sel)[0].text is a JSON string."""
    return types.SimpleNamespace(
        html=types.SimpleNamespace(
            find=lambda sel: [types.SimpleNamespace(text=json.dumps(payload))]
        )
    )


def card(home="Boston Celtics", away="New York Knicks", home_score=110, away_score=105):
    """One well-formed game card, shaped like the real nba.com payload."""

    def leader(tricode, name, points, rebounds, assists):
        return {
            "personId": 1,
            "name": name,
            "jerseyNum": "23",
            "position": "PF",
            "teamTricode": tricode,
            "playerSlug": name.lower().replace(" ", "-"),
            "points": points,
            "rebounds": rebounds,
            "assists": assists,
        }

    return {
        "cardData": {
            "seasonType": "Regular Season",
            "homeTeam": {
                "wins": 10,
                "losses": 5,
                "teamName": home,
                "score": home_score,
                "teamLeader": leader("BOS", "Player One", "30", "5", "7"),
            },
            "awayTeam": {
                "wins": 8,
                "losses": 7,
                "teamName": away,
                "score": away_score,
                "teamLeader": leader("NYK", "Player Two", "25", "8", "4"),
            },
        }
    }


def payload(cards):
    return {"props": {"pageProps": {"gameCardFeed": {"modules": [{"cards": cards}]}}}}


def run_case(name, data, expect_results, expect_type):
    async def go():
        async def fake_get_url(url):
            return fake_response(data)

        generator.get_url = fake_get_url
        # The highlight lookup hits the network; keep it out of these checks.
        generator.generate_youtube_video_link = lambda *a, **k: _empty()
        return await generator.generate_result()

    async def _empty():
        return ()

    results, games_type = asyncio.run(go())

    assert len(results) == expect_results, (
        f"{name}: expected {expect_results} results, got {len(results)}"
    )
    assert games_type == expect_type, (
        f"{name}: expected games_type {expect_type!r}, got {games_type!r}"
    )
    print(f"PASS  {name}")


# 1. No games that day: nba.com returns an empty modules list (e.g. Thanksgiving).
run_case(
    "no games -> modules empty",
    {"props": {"pageProps": {"gameCardFeed": {"modules": []}}}},
    expect_results=0,
    expect_type=None,
)

# 2. Modules present but the cards list is empty.
run_case(
    "no games -> cards empty",
    {"props": {"pageProps": {"gameCardFeed": {"modules": [{"cards": []}]}}}},
    expect_results=0,
    expect_type=None,
)

# 3. A card without the expected shape must degrade, not crash.
run_case(
    "malformed card -> degrades",
    payload([{}]),
    expect_results=0,
    expect_type=None,
)

# 4. One good card among broken ones still produces a result.
run_case(
    "good card survives broken neighbours",
    payload([card(), {"cardData": {"homeTeam": None, "awayTeam": None}}, {}]),
    expect_results=1,
    expect_type="Regular Season",
)

# 5. The season type is taken from the first card that has one.
run_case(
    "season type from first valid card",
    payload([{}, card(), card()]),
    expect_results=2,
    expect_type="Regular Season",
)

# 6. A card whose teams are None (TBD games) is skipped, the rest still post.
run_case(
    "TBD card skipped, others kept",
    payload([card(home="A", away="B"), {"cardData": {"seasonType": "in-season-knockout",
                                                    "homeTeam": None, "awayTeam": None}}]),
    expect_results=1,
    expect_type="Regular Season",
)

def check_timeout_and_off_loop():
    """get_url must pass a timeout and must not block the event loop."""
    seen = {}

    class SlowSession:
        def get(self, url, **kwargs):
            seen.update(kwargs)
            time.sleep(0.5)  # a real hung connection
            return fake_response({})

    original = generator.asession
    generator.asession = SlowSession()
    generator.get_url = real_get_url

    async def go():
        ticks = 0

        async def ticker():
            nonlocal ticks
            while True:
                ticks += 1
                await asyncio.sleep(0.01)

        spin = asyncio.ensure_future(ticker())
        await generator.get_url("https://example.invalid")
        spin.cancel()

        return ticks

    try:
        ticks = asyncio.run(go())
    finally:
        generator.asession = original
        generator.get_url = real_get_url

    assert seen.get("timeout") == generator.REQUEST_TIMEOUT, (
        f"expected timeout={generator.REQUEST_TIMEOUT}, got {seen.get('timeout')!r}"
    )
    assert ticks > 5, (
        f"event loop was blocked during the fetch (only {ticks} ticks ran)"
    )
    print("PASS  timeout is passed and the event loop keeps running")


check_timeout_and_off_loop()
print("ALL CHECKS PASSED")
