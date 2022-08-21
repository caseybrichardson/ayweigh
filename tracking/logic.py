import datetime
import logging
from typing import Optional

import discord
from asgiref.sync import sync_to_async
from django.core.files.base import ContentFile

from django.utils import timezone

from tracking.models import Contest, CheckIn, ContestantCheckIn, Contestant, CheckInPhoto

logger = logging.getLogger(__name__)


async def initialize_contest(contest: Contest):
    # Create all the needed check-ins
    time_interval = datetime.timedelta(days=contest.check_in_period)
    final_check_in = contest.final_check_in

    # Contest starting date is the first check-in, then create a check-in every `time_interval` days, until
    # the date is >= `final_check_in`
    await CheckIn.objects.acreate(
        contest=contest,
        starting=contest.starting
    )

    # Create the intermediate check-ins
    current_date = contest.starting + time_interval
    while current_date < final_check_in:
        await CheckIn.objects.acreate(
            contest=contest,
            starting=current_date
        )
        current_date = current_date + time_interval

    # Create the final check-in if the last date we were on is not the final date of the contest
    if current_date != final_check_in:
        await CheckIn.objects.acreate(
            contest=contest,
            starting=final_check_in
        )


async def initialize_check_in(check_in: CheckIn, bot: 'tracking.bot.WeighbotClient'):
    channel_id = int(check_in.contest.channel_id)
    channel = bot.get_channel(channel_id)
    thread = await channel.create_thread(
        name=f'Check-in {check_in.starting}',
        type=discord.ChannelType.public_thread,
        auto_archive_duration=1440
    )

    check_in.started_at = timezone.now()
    check_in.thread_id = thread.id
    await sync_to_async(check_in.save, thread_sensitive=True)()

    await thread.send('Send a message with your weight in pounds, and any images you want to share')
    # Once initialized, the bot should route and handle messages using DB lookups on the thread ID.
    # The check-in will be closed by the update polling.


async def log_check_in(message: discord.Message, check_in: Optional[CheckIn]):
    logger.info('Logging check-in: %s in %s', message, check_in)
    if check_in is None:
        check_in = await CheckIn.objects.aget(thread_id=message.channel.id)

    contestant = await Contestant.objects.aget(discord_id=str(message.author.id))

    contestant_check_in = await ContestantCheckIn.objects.acreate(
        discord_id=message.id,
        check_in=check_in,
        contestant=contestant,
        weight=float(message.content)
    )

    logger.info('Attachments contain: %s', message.attachments)
    for attachment in message.attachments:
        data = await attachment.read()
        with ContentFile(data, name=attachment.filename) as file_attachment:
            await CheckInPhoto.objects.acreate(
                discord_id=attachment.id,
                kind='check-in',
                contestant_check_in=contestant_check_in,
                image=file_attachment
            )
        logger.info('Attachment is: %s', attachment)


async def get_startable_check_in(contest: Contest):
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
