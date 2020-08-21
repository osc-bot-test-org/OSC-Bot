import asyncio
from config import Config
import discord.ext.commands.errors
from github import Github, UnknownObjectException
from os import environ

# Used emojis
CHECK_MARK_EMOJI = '\U0001F973'
RESTART_EMOJI = '\U0001F504'
THUMBS_UP_EMOJI = '\N{THUMBS UP SIGN}'

# Some constants related to program logic
# TODO: Add them in DB with commands to change them
GITHUB_SLEEP_TIME = 30
GITHUB_REQ_PERCENTAGE = 80 / 100

# github data
github_token = environ.get('GITHUB_TOKEN')
org_name = environ.get('ORG_NAME')


# TODO: let the bot ask the remaining members for their GitHubs if it was down during the GitHub collection process


# Setup function
def setup_member_interface(bot):
    # -------------------------------- Getting info --------------------------------
    # Show channels
    @bot.command(brief="Shows all the channels that are related to the voting process")
    async def channels(ctx):
        chans = Config.channels()
        msgs = [f'{name} is <#{chans[name]}>' for name in chans.keys()]
        msg = '\n'.join(msgs)
        await ctx.send(msg)

    @bot.command(brief="Shows information about the voting process")
    async def voting_info(ctx):
        time_to_wait = Config.get('time-to-wait')
        req_votes = Config.get('required-votes')
        await ctx.send(f'The current voting period is {time_to_wait} seconds.\n' +
                       f'The required votes for each idea are {req_votes} votes.')

    # -------------------------------- Voting logic --------------------------------
    # Proposes a new idea to idea channel
    @bot.command(brief="Adds a new idea to the ideas channel")
    async def new_idea(ctx, lang='', idea_name='', idea_explanation='N/A'):

        # Check fields
        if not lang or not idea_name:
            return await ctx.send(f'{ctx.author.mention} fields are invalid! ' +
                                  'Please use "language" "idea name" "idea explanations" as arguments')

        if len(idea_name) > 100:
            return await ctx.send(ctx.author.mention + ", the idea name length must be less that 100 characters long")

        # Get channel
        chanid = Config.get('idea-channel')
        chanid = int(chanid)
        chan = bot.get_channel(chanid)
        overview_id = int(Config.get('overview-channel'))
        overview_channel = bot.get_channel(overview_id)
        if not chanid:
            return await ctx.send('Idea channel is not available!')

        # Generate a name from idea
        gen_name = '-'.join(idea_name.split(' ')).lower()
        for item in ['`', '"', '*', '_', '@']:  # Filter out unwanted characters
            lang = lang.replace(item, '')
            idea_explanation = idea_explanation.replace(item, '')
            gen_name = gen_name.replace(item, '')

        # Check if there is an idea team with the current idea
        role = discord.utils.get(ctx.guild.roles, name=gen_name)
        if role:
            return await ctx.send(ctx.author.mention + ", this idea name already exists.")

        # Check if there is currently a proposed idea with the same title
        messages = await chan.history().flatten()
        for message in messages:
            if message.embeds and message.embeds[0].title == gen_name:
                return await ctx.send(ctx.author.mention + ", this idea name already exists.")

        try:
            # Notify with embed
            embed = discord.Embed(title=gen_name, color=0x00ff00)
            embed.add_field(name="Idea Explanation", value=idea_explanation)
            embed.add_field(name='Programming Language', value=lang, inline=False)
            msg = await chan.send(f'{ctx.author.mention} proposed an idea, please vote using a thumbs up reaction:',
                                  embed=embed)
            await msg.add_reaction('👍')

            # Watch it
            await wait_for_votes(msg.id, gen_name)
        except discord.HTTPException:
            await overview_channel.send(ctx.author.mention +
                                        ", an error has occurred while processing one of your ideas")

    # Asks user for github
    async def get_github(voter, gen_name):
        embed = discord.Embed(title=gen_name)
        embed.add_field(name="Idea", value=gen_name)
        embed.add_field(name="Guild ID", value=voter.guild.id)
        await voter.send('Hello!\nWe noticed that you have voted for the following idea:\n' +
                         'Please send me your GitHub username so I can add you to the team.', embed=embed)

    async def get_all_githubs(participants, gen_name, message):
        guild = message.guild
        role = await guild.create_role(name=gen_name)  # Creates a role for the team

        for user in participants:
            if not user.bot:
                await get_github(user, gen_name)  # Asks each user for their Github
            else:
                await user.add_roles(role)  # Adds the role to the bot

        await asyncio.sleep(GITHUB_SLEEP_TIME)

        overview_id = int(Config.get('overview-channel'))
        overview_channel = bot.get_channel(overview_id)
        # If the required percentage or more replied with their GitHub accounts and got their roles added
        if len(role.members) >= GITHUB_REQ_PERCENTAGE * len(participants):
            await overview_channel.send(f'More than {GITHUB_REQ_PERCENTAGE * 100}%' +
                                        f'of the participants in `{gen_name}` ' +
                                        'replied with their GitHub usernames, idea approved!')
            await message.delete()
            # TODO: Create a category and channels for them
            # TODO: Give the role the permission to access this category
            # TODO: Create GitHub team in the organization
            # TODO: Create GitHub repo in the organization
        else:
            await overview_channel.send(
                f'Less than {GITHUB_REQ_PERCENTAGE * 100}% of the participants in `{gen_name}` '
                + "replied with their GitHub usernames, idea cancelled.")
            await role.delete()
            await message.delete()

    # Watches a vote for 14 days
    async def wait_for_votes(message_id, gen_name):

        # Get channels
        overview_chan = Config.get('overview-channel')
        overview_chan = int(overview_chan)
        overview_chan = bot.get_channel(overview_chan)
        idea_id = int(Config.get('idea-channel'))
        idea_channel = bot.get_channel(idea_id)
        msg = None

        # Trial count
        for _ in range(4):
            time_to_wait = int(Config.get('time-to-wait'))
            # Wait for 14 days
            await asyncio.sleep(time_to_wait)
            msg = await idea_channel.fetch_message(message_id)
            voters_number = 0
            participants = msg.mentions[0].mention  # Add the idea owner as an initial participant
            participants_list = [msg.mentions[0]]  # A list to contain Members
            for reaction in msg.reactions:
                if reaction.emoji == THUMBS_UP_EMOJI:
                    users = await reaction.users().flatten()  # Find the users of this reaction
                    voters_number = len(users)
                    for user in users:
                        if user == msg.mentions[0]:  # If the user is the owner of the idea, continue
                            continue
                        participants += "\n" + user.mention
                        participants_list.append(user)

            req_votes = int(Config.get('required-votes'))
            # Check votes (-1 the bot)
            if voters_number > req_votes:
                await msg.delete()
                embed = discord.Embed(title=gen_name)
                participants_message = await overview_chan.send(
                    f'''
                    {CHECK_MARK_EMOJI * voters_number}\n\n''' +
                    f'''Voting for {gen_name} has ended, **approved**!\n'''
                    f'''Participants:\n{participants}\nPlease check your messages
                    ''', embed=embed)
                return await get_all_githubs(participants_list, gen_name, participants_message)

            # If the votes aren't enough
            await overview_chan.send(
                f'Votes for `{gen_name}` were not enough, waiting for more votes...'
            )
            continue  # Wait 14 days more

        # Trials end here
        await overview_chan.send(
            f'The `{gen_name}` idea has been cancelled due to lack of interest :('
        )

        # Delete the message
        await msg.delete()

    # -------------------------------- Bot Events --------------------------------
    # Startup
    @bot.event
    async def on_ready():
        print('I\'m alive, my dear human :)')
        print("Checking for any unfinished ideas...")

        idea_id = int(Config.get('idea-channel'))
        idea_channel = bot.get_channel(idea_id)
        messages = await idea_channel.history().flatten()
        for message in messages:  # Loop through the messages in the ideas channel
            if message.embeds:  # If the message is an idea message containing Embed, add the restart emoji
                print("Found an unfinished idea!")
                await message.add_reaction(RESTART_EMOJI)

        print("No unfinished ideas since last boot")

    # Watch for reaction add
    @bot.event
    async def on_raw_reaction_add(reaction):
        idea_id = int(Config.get('idea-channel'))
        idea_channel = bot.get_channel(idea_id)
        overview_id = int(Config.get('overview-channel'))
        overview_channel = bot.get_channel(overview_id)

        if reaction.channel_id != idea_id:  # Makes sure the reaction added is in the ideas channel
            return

        message = await idea_channel.fetch_message(reaction.message_id)
        if message.author.bot and message.embeds:  # If the message reacted to is by the bot and contains an embed
            # ie: it is an idea message
            embed = message.embeds[0]

            if reaction.emoji.name == THUMBS_UP_EMOJI:
                return

            elif reaction.emoji.name == RESTART_EMOJI and reaction.member.bot:
                # if it is a restart emoji put by the bot, restart the voting period
                idea_name = embed.title
                await overview_channel.send(f'An error occurred while processing the `{idea_name}` idea\n' +
                                            "The voting period has been restarted but your votes are safe.")
                # We remove the reaction in case the voting period gets restarted again
                await message.remove_reaction(reaction.emoji, reaction.member)
                await wait_for_votes(message.id, idea_name)

            else:  # If it is another emoji, remove the reaction
                await message.remove_reaction(reaction.emoji, reaction.member)

    # Watch for reaction remove
    @bot.event
    async def on_reaction_remove(reaction, member):
        message = reaction.message
        idea_id = int(Config.get('idea-channel'))
        if message.channel.id == idea_id and message.author.bot and reaction.emoji == THUMBS_UP_EMOJI:
            if member == message.mentions[0]:  # If the reaction remover is the owner of the idea
                users = await reaction.users().flatten()
                replacer = "No owner "
                if len(users) > 1:  # There are voters other than the bot
                    bot_replace = False
                else:
                    bot_replace = True

                for user in users:  # Replace with bot if there aren't votes, otherwise replace with user
                    if user.bot == bot_replace:
                        replacer = user.mention

                new_content = message.content.replace(message.mentions[0].mention, replacer)
                await message.edit(content=new_content)
                # Replace the owner with the voter

    # Watch messages addition to check for sent GitHub accounts
    @bot.event
    async def on_message(message):
        channel = message.channel
        found_idea = False
        if channel.type != discord.ChannelType.private:  # If it is not a DM Channel
            return await bot.process_commands(message)  # Process the commands normally

        if message.author.bot:
            return

        messages = await channel.history().flatten()  # Get last 100 messages in DM channel

        # Variables initial declaration
        gen_name = ''
        embed = None
        guild_id = 0

        for message in messages:
            if message.embeds:  # If it is an idea message containing an embed
                found_idea = True
                embed = message.embeds[0]
                gen_name = embed.title  # Gets the idea name from the message sent to user
                break

        if not found_idea:
            return

        for field in embed.fields:
            if field.name == "Guild ID":
                guild_id = int(field.value)

        guild = bot.get_guild(guild_id)  # Gets the server

        # Checking if team creation process was done
        await channel.send("Please wait...")
        overview_channel_id = int(Config.get('overview-channel'))
        overview_channel = bot.get_channel(overview_channel_id)
        participants_messages = await overview_channel.history().flatten()
        idea_ended = False

        for message in participants_messages:
            if message.embeds and message.embeds[0].title == gen_name:
                # If it is a participants messages containing an Embed
                break
            idea_ended = True

        if idea_ended:
            return await channel.send("The team creation process for this idea has already ended.\n" +
                                      "Please contact an administrator if you would like to join the team.")

        # Checking the username and adding to the server
        username_message = messages[0]  # Gets the last message in DM (the one containing the username)

        g = Github(github_token)  # Logs into GitHub
        try:
            github_user = username_message.content
            g.get_user(github_user)  # Tries to find the user on GitHub
            role = discord.utils.get(guild.roles, name=gen_name)  # Finds the role created in get_all_githubs function

            # Gets information from the server
            guild_user = guild.get_member(username_message.author.id)
            if not guild_user:
                return await channel.send("I can't find you in the server, have you left?")
            github_channel_id = int(Config.get('github-channel'))
            github_channel = guild.get_channel(github_channel_id)

            # Puts the information in the server
            await guild_user.add_roles(role)  # Adds the role
            embed = discord.Embed(title=github_user)  # Creates an embed with the GitHub username as title
            embed.add_field(name="Idea team", value=gen_name)  # Idea team name (gen_name) as a field
            await github_channel.send(guild_user.mention, embed=embed)  # Send to the GitHub channel in the server
            await channel.send("Thank you!")
        except UnknownObjectException:  # If the user's GitHub was not found
            await channel.send("This username is not a valid Github username")
