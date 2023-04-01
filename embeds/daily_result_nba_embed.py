import discord
from emojis.find_emojis import find_emojis
from generate_information.generator import generate_link


def generate_result_embed(date_today, logo_url):
    embed = discord.Embed(
        title=f"NBA Results for {date_today}",
        colour=discord.Colour.blue(),
    )
    embed.set_thumbnail(url=logo_url)

    return embed


async def generate_result_field_for_embed(ctx, show, embed):

    home_sing, away_sing = (
        ("", await find_emojis(ctx, "9410pinkarrowL"))
        if show["Home"]["Team"]["score"] > show["Away"]["Team"]["score"]
        else (await find_emojis(ctx, "9410pinkarrowR"), "")
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
        f"{await find_emojis(ctx, 'youtube')} **Highlights** {', '.join([await generate_link(f'Link {pos}', link) for pos, link in enumerate(show['Highlights'], 1)])}",
        inline=False,
    )
