from datetime import time
from zoneinfo import ZoneInfo


import discord
import date.date_manipulations as date
import os
import generate_information.generator as generate

from discord.ext import commands, tasks
from embeds.daily_result_nba_embed import (
    generate_result_embed,
    generate_result_field_for_embed,
)
local_tz = ZoneInfo("Europe/Sofia")   # 08:30 local, DST-proof

class ClientInit(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(command_prefix="!", help_command=None, intents=intents)

    async def on_ready(self):
        #await self.test_results()
        # on_ready fires again on every reconnect, and starting a running task raises.
        if not self.scheduler_results.is_running():
            self.scheduler_results.start()

    def scheduler_results_unload(self):
        self.scheduler_results.cancel()

    async def test_results(self):
        try:
            embed_result = await show_result(
                self.get_channel(int(os.getenv("MAIN_CHANNEL_DISCORD")))
            )

            if not embed_result:
                return

            for id_channel in await get_all_channels_id(self):
                # dev test func
                if not int(os.getenv("TEST_CHANNEL_DISCORD")) == id_channel:
                    continue

                ctx = self.get_channel(id_channel)
                for embed in embed_result:
                    try:
                        await ctx.send(embed=embed)
                    except Exception as e:
                        print(f"An error occurred id {id_channel}: {e}")
        except Exception as e:
            print(f"Exception in the task_loop: {e}")


    @tasks.loop(time=time(hour=8, minute=30, tzinfo=local_tz))
    async def scheduler_results(self):
        try:
            embed_result = await show_result(
                self.get_channel(int(os.getenv("MAIN_CHANNEL_DISCORD")))
            )

            if not embed_result:
                return

            for id_channel in await get_all_channels_id(self):
                # dev test func
                # if not int(os.getenv("TEST_CHANNEL_DISCORD")) == id_channel:
                #     continue

                ctx = self.get_channel(id_channel)
                for embed in embed_result:
                    try:
                        await ctx.send(embed=embed)
                    except Exception as e:
                        print(f"An error occurred id {id_channel}: {e}")
        except Exception as e:
            print(f"Exception in the task_loop: {e}")


client = ClientInit()


async def get_all_channels_id(client: client) -> tuple:
    return (
        channel.id
        for server in client.guilds
        for channel in server.channels
        if os.getenv("DISCORD_CHANNEL_NAME") in channel.name
    )


async def show_result(ctx: client) -> discord.Embed:
    today_, nba_score_results, games_type = (
        await date.get_current_date(),
        *await generate.generate_result(),
    )

    if not nba_score_results:
        return
    print(f"data => {today_}")
    print(nba_score_results)
    print(f"games type => {games_type}")
    
    embeds = [generate_result_embed(today_, os.getenv("NBA_LOGO"), games_type)]
    for show in nba_score_results[:8]:
        await generate_result_field_for_embed(ctx, show, embeds[0])

    if len(nba_score_results) > 8:
        embeds.append(generate_result_embed(today_, os.getenv("NBA_LOGO"), games_type))
        for show in nba_score_results[8:]:
            await generate_result_field_for_embed(ctx, show, embeds[1])

    return embeds


# @tasks.loop(seconds=0)
# async def task_loop() -> None:
#     try:
#         embed_result = await show_result(
#             client.get_channel(int(os.getenv("MAIN_CHANNEL_DISCORD")))
#         )
#
#         if not embed_result:
#             return
#
#         for id_channel in await get_all_channels_id(client):
#             # if not int(os.getenv("TEST_CHANNEL_DISCORD")) == id_channel:  # dev test func
#             ctx = client.get_channel(id_channel)
#             for embed in embed_result:
#                 try:
#                     await ctx.send(embed=embed)
#                 except Exception as e:
#                     print(f"An error occurred id {id_channel}: {e}")
#     except Exception as e:
#         print(f"Exception in the task_loop: {e}")


# @client.command()
# async def nba_start(ctx: client, time_value: float) -> None:
#     if str(ctx.author) == os.getenv("OWNER"):
#         task_loop.change_interval(hours=float(time_value))
#         if task_loop.next_iteration:
#             task_loop.cancel()
#         await ctx.send(
#             f"```It's set on every {int(time_value)}h to show the results!```"
#         )
#         task_loop.start()


# @client.command()
# async def live(ctx: client) -> None:
#     live_games = await generate.scrape_all_games(os.getenv("NBA"))
#
#     embed = discord.Embed(
#         title=f"NBA Live Games",
#         colour=discord.Colour.blue(),
#     )
#     embed.set_thumbnail(url=os.getenv("RESULT_LIVE_LOGO"))
#
#     for k, v in live_games.items():
#         away_team, home_team = await generate.get_nba_team_names(k)
#         embed.add_field(
#             name=f"{await find_emojis(ctx, away_team)} **{k}** {await find_emojis(ctx, home_team)}",
#             value=f"{await find_emojis(ctx, '3716_ArrowRightGlow')} {', '.join(await generate.generate_link_correct_len(v))}",
#             inline=False,
#         )
#
#     await ctx.send(embed=embed)


client.run(os.getenv("TOKEN"))
