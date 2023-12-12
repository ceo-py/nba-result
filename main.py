import discord
import date.date_manipulations as date
import os
import generate_information.generator as generate

from discord.ext import commands, tasks
from embeds.daily_result_nba_embed import (
    generate_result_embed,
    generate_result_field_for_embed,
)

client = commands.Bot(
    command_prefix="!", help_command=None, intents=discord.Intents.all()
)


async def get_all_channels_id(client: client) -> tuple:
    return (
        channel.id
        for server in client.guilds
        for channel in server.channels
        if os.getenv("DISCORD_CHANNEL_NAME") in channel.name
    )


async def show_result(ctx: client) -> discord.Embed:
    today_, nba_score_results = (
        await date.get_current_date(),
        await generate.generate_result(),
    )

    if not nba_score_results:
        return

    embeds = [generate_result_embed(today_, os.getenv("NBA_LOGO"))]
    for show in nba_score_results[:8]:
        await generate_result_field_for_embed(ctx, show, embeds[0])

    if len(nba_score_results) > 8:
        embeds.append(generate_result_embed(today_, os.getenv("NBA_LOGO")))
        for show in nba_score_results[8:]:
            await generate_result_field_for_embed(ctx, show, embeds[1])

    return embeds


@tasks.loop(seconds=0)
async def task_loop() -> None:
    try:
        embed_result = await show_result(
            client.get_channel(int(os.getenv("MAIN_CHANNEL_DISCORD")))
        )

        if not embed_result:
            return

        for id_channel in await get_all_channels_id(client):
            # if not int(os.getenv("TEST_CHANNEL_DISCORD")) == id_channel:  # dev test func
                ctx = client.get_channel(id_channel)
                for embed in embed_result:
                    try:
                        await ctx.send(embed=embed)
                    except Exception as e:
                        print(f"An error occurred id {id_channel}: {e}")
    except Exception as e:
        print(f"Exception in the task_loop: {e}")


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
