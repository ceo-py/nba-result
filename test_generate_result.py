"""Self-check for generate_result() edge cases. No network, no pytest needed.

Run from the repo root: venv/bin/python test_generate_result.py
"""
import asyncio
import json
import sys
import types

sys.path.insert(0, ".")

# Stub requests_html so this check runs without the real dependency installed.
fake = types.ModuleType("requests_html")
fake.HTMLSession = lambda: types.SimpleNamespace(get=lambda url: None)
sys.modules["requests_html"] = fake

from generate_information import generator


def fake_response(payload):
    """Shape like requests_html: response.html.find(sel)[0].text is a JSON string."""
    return types.SimpleNamespace(
        html=types.SimpleNamespace(
            find=lambda sel: [types.SimpleNamespace(text=json.dumps(payload))]
        )
    )


def run_case(name, payload, expect_results, expect_type):
    async def go():
        generator.get_url = lambda url: fake_response(payload)
        return await generator.generate_result()

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
    {"props": {"pageProps": {"gameCardFeed": {"modules": [{"cards": [{}]}]}}}},
    expect_results=0,
    expect_type=None,
)

print("ALL CHECKS PASSED")
