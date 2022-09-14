import logging
from typing import Optional

import discord
from discord import app_commands
from asgiref.sync import sync_to_async
from tracking.analysis import generate_personal_progress_report

from tracking.constants import Units
from tracking.errors import ChannelNotFound, ContestantNotFound, NoContestRunning, ContestantAlreadyJoined
from tracking.logic import log_weight, join_contestant_to_contest
from tracking.checks import origin_is_active_check_in

logger = logging.getLogger(__name__)


class WeighbotClient(discord.Client):
    def __init__(self, *, intents, **options):
        super(WeighbotClient, self).__init__(intents=intents, **options)
        self.tree = discord.app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()

    async def on_ready(self):
        logger.info('Bot is ready')


intents = discord.Intents.default()
intents.message_content = True
client = WeighbotClient(intents=intents)


@client.tree.command(
    description='Non-functional at the moment.'
)
async def start_contest(interaction: discord.Interaction):
    pass


@client.tree.command(
    description='Functional only in channels where there is an active contest. Joins you to the contest.'
)
async def join_contest(interaction: discord.Interaction):
    try:
        await join_contestant_to_contest(interaction.channel_id, interaction.user.id, interaction.user.name)
        # TODO: Create multiple message endings?
        await interaction.response.send_message(f'{interaction.user.name} has entered the fray!')
    except NoContestRunning:
        await interaction.response.send_message('There is no contest running in this channel.', ephemeral=True)
    except ContestantAlreadyJoined:
        await interaction.response.send_message('There is no contest running in this channel.', ephemeral=True)


@client.tree.command(
    description='Functional only in check-in threads. Submits your current weight for contest tracking.',
    extras={
        'check_in_only': True
    }
)
@app_commands.describe(
    weight='Your current weight',
    units='The units for your weight. Defaults to lbs.',
    image='An optional image of your progress.'
)
@app_commands.check(origin_is_active_check_in)
async def weigh_in(
    interaction: discord.Interaction,
    weight: float,
    units: Units = Units.lbs,
    image: Optional[discord.Attachment] = None
):
    try:
        overall, latest = await log_weight(interaction.channel_id, interaction.user.id, weight, units.value, image)
    except ChannelNotFound:
        await interaction.response.send_message('There is no check-in currently running in this channel or thread.')
        return
    except ContestantNotFound:
        await interaction.response.send_message('You are not enrolled in a contest currently.')
        return

    user_name = interaction.user.name
    if overall and latest:
        since_start_comparison = 'up' if overall >= 0 else 'down'
        since_last_comparison = 'up' if latest >= 0 else 'down'
        overall_str = f'{since_start_comparison} {abs(overall):.1f}lbs overall'
        latest_str = f'{since_last_comparison} {abs(latest):.1f}lbs since the last check-in'
        message = f'{user_name}, you are {overall_str} and {latest_str}.'
        await interaction.response.send_message(message)
    else:
        await interaction.response.send_message(f'{user_name}, your starting weight is {weight}')


# TODO: Make the below stubs functional once the analytics functions are ready


@client.tree.command(
    description='Non-functional at the moment.'
)
async def personal_progress(
    interaction: discord.Interaction,
):
    user_id = interaction.user.id
    channel_id = interaction.channel_id
    try:
        image = await sync_to_async(generate_personal_progress_report, thread_sensitive=True)(user_id, channel_id)
        image_file = discord.File(image, 'personal_progress.png')
        await interaction.response.send_message('Your current progress!', file=image_file)
    except Exception:
        logger.exception('Error during personal-progress generation')
        await interaction.response.send_message('Sorry, there was an issue generating your graph!')


@client.tree.command(
    description='Non-functional at the moment.'
)
async def contest_progress(
    interaction: discord.Interaction,
):
    await interaction.response.send_message('The current contest progress!')
