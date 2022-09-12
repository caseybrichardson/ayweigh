import datetime
import logging
from typing import Optional

import discord
from discord.types import snowflake
import django.db
from asgiref.sync import sync_to_async
from django.core.files.base import ContentFile
from django.utils import timezone

from tracking.constants import Units
from tracking.errors import ChannelNotFound, ContestantNotFound, ContestantAlreadyJoined, NoContestRunning
from tracking.models import *

logger = logging.getLogger(__name__)


async def initialize_contest(contest: Contest):
    # Create all the needed check-ins
    time_interval = datetime.timedelta(days=contest.check_in_period)
    final_check_in = contest.final_check_in

    # Contest starting date is the first check-in, then create a check-in every `time_interval` days, until
    # the date is >= `final_check_in`
    previous = await CheckIn.objects.acreate(
        contest=contest,
        starting=contest.starting
    )

    # Create the intermediate check-ins
    current_date = contest.starting + time_interval
    while current_date < final_check_in:
        check_in = await CheckIn.objects.acreate(
            contest=contest,
            starting=current_date,
            previous=previous
        )
        previous = check_in
        current_date = current_date + time_interval

    # Create the final check-in if the last date we were on is not the final date of the contest
    if current_date != final_check_in:
        await CheckIn.objects.acreate(
            contest=contest,
            starting=final_check_in
        )


async def initialize_check_in(check_in: CheckIn, bot: 'tracking.bot.WeighbotClient'):
    channel_id = int(check_in.contest.channel_id)
    channel: discord.TextChannel = bot.get_channel(channel_id)

    # Sometimes this fails. There might be sync issues, so we'll attempt this again later.
    if channel is None:
        return

    try:
        start = await channel.send(f'Check-in {check_in.starting} is starting!')
        thread = await channel.create_thread(
            name=f'Check-in',
            message=start,
            type=discord.ChannelType.public_thread,
            auto_archive_duration=1440
        )
    except discord.errors.DiscordException:
        logger.exception('Failure creating thread')
        return

    check_in.started_at = timezone.now()
    check_in.thread_id = thread.id
    try:
        await sync_to_async(check_in.save, thread_sensitive=True)()
    except django.db.Error:
        logger.exception('Error saving check-in start, %s', check_in)
        return

    await thread.send(
        'Send a message with your weight in pounds, and any images you want to share (all in the same message)'
    )
    # Once initialized, the bot should route and handle messages using DB lookups on the thread ID.
    # The check-in will be closed by the update polling.


async def join_contestant_to_contest(
        channel_id: snowflake,
        user_id: snowflake,
        name: snowflake
):
    try:
        await Contestant.objects.aget(
            discord_id=str(user_id),
            contest__channel_id=str(channel_id)
        )
        raise ContestantAlreadyJoined('Contestant has already joined the contest')
    except Contestant.DoesNotExist:
        pass

    try:
        contest = await Contest.objects.aget(
            channel_id=channel_id
        )
    except Contest.DoesNotExist:
        raise NoContestRunning('There is no contest running in this channel')

    logger.info('Joining user: %s %s to %s', user_id, name, channel_id)
    await Contestant.objects.acreate(
        name=name,
        discord_id=user_id,
        contest=contest
    )


async def log_weight(
        channel_id: snowflake,
        user_id: snowflake,
        weight: float,
        units: Units,
        attachment: Optional[discord.Attachment]
):
    try:
        check_in = await CheckIn.objects.select_related('contest').aget(thread_id=channel_id)
    except CheckIn.DoesNotExist:
        raise ChannelNotFound('No active check-in found for this channel')

    try:
        contestant = await Contestant.objects.aget(
            discord_id=str(user_id),
            contest__channel_id=check_in.contest.channel_id
        )
    except Contestant.DoesNotExist:
        raise ContestantNotFound('Current user is not a contestant')

    contestant_check_in, _ = await ContestantCheckIn.objects.aupdate_or_create(
        check_in=check_in,
        contestant=contestant,
        defaults={
            'weight': weight,
            'units': units,
            'discord_id': '',
        }
    )

    overall, since_last = await get_weight_diffs(contestant)

    if attachment is not None:
        data = await attachment.read()
        with ContentFile(data, name=attachment.filename) as file_attachment:
            photo = await CheckInPhoto.objects.acreate(
                discord_id=attachment.id,
                kind='check-in',
                contestant_check_in=contestant_check_in,
                image=file_attachment
            )
            logger.info('Handled attachment %s: %s', attachment.id, photo)

    return overall, since_last


async def get_startable_check_in(contest: Contest) -> Optional[CheckIn]:
    current_date = timezone.now().date()

    try:
        check_in = await contest.check_ins.filter(
            finished=False,
            thread_id__isnull=True,
            starting__lte=current_date
        ).aearliest('starting')
        return check_in
    except CheckIn.DoesNotExist:
        return None


async def get_running_check_in(contest: Contest) -> Optional[CheckIn]:
    try:
        check_in = await contest.check_ins.filter(
            finished=False,
            thread_id__isnull=False,
            started_at__isnull=False
        ).aearliest('starting')
        return check_in
    except CheckIn.DoesNotExist:
        return None


async def get_weight_diffs(contestant: Contestant) -> (float, float):
    first: ContestantCheckIn = await contestant.check_ins.aearliest('check_in__starting')
    last: ContestantCheckIn = await contestant.check_ins.select_related('check_in').alatest('check_in__starting')
    try:
        previous: ContestantCheckIn = await contestant.check_ins.filter(check_in__starting__lt=last.check_in.starting).alatest('check_in__starting')
    except ContestantCheckIn.DoesNotExist:
        return last.weight - first.weight, None
    # TODO: Normalize weights, what if someone decides to mix units?
    return last.weight - first.weight, last.weight - previous.weight

