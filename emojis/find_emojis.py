async def find_emojis(ctx, look_for_emoji: str) -> str:
    for emoji in ctx.guild.emojis:
        if look_for_emoji.split()[-1] in emoji.name:
            return str(emoji)
    return ""
