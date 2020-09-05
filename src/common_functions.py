import re
import discord


async def get_gen_name(idea_name):
    if len(idea_name) > 95:
        return None
    gen_name = '-'.join(idea_name.split(' ')).lower()
    gen_name = re.sub("([^a-z-])+", '', gen_name)  # Remove anything that is not a letter
    gen_name = re.sub("(-)+", '-', gen_name)  # Replace multiple dashes with a single one
    gen_name = gen_name[:-1] if gen_name[-1] == "-" else gen_name
    return gen_name


async def check_team_existence(ctx, team_name, roles):
    author_mention = ctx.author.mention
    role = discord.utils.get(roles, name=team_name)
    category = discord.utils.get(ctx.guild.categories, name=team_name)

    if not category or not role:
        await ctx.send(author_mention + ", invalid team name")
        return None

    if role.permissions.administrator:
        await ctx.send(author_mention + ", you can't do that")
        return None

    return role
