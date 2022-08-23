import asyncio
import logging
from typing import List

import discord
from asgiref.sync import sync_to_async
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.management import BaseCommand
from django.utils import timezone

from tracking.bot import WeighbotClient
from tracking.logic import initialize_contest, initialize_check_in, get_startable_check_in, get_running_check_in
from tracking.models import Contest

logger = logging.getLogger(__name__)


async def poll_for_updates(bot: 'tracking.bot.WeighbotClient'):
    while True:
        logger.info('Polling contest updates')
        current_datetime = timezone.now()
        try:
            # Update all our un-finished contests
            contests = Contest.objects.filter(
                finished=False
            ).prefetch_related('check_ins')

            async for contest in contests:
                # Is this contest un-initialized?
                check_in_count = await contest.check_ins.acount()
                if check_in_count == 0:
                    logger.info('Initializing contest %s', contest)
                    await initialize_contest(contest)

                # If we have a running check_in, then only update that.
                # Otherwise, look for and initialize check_ins that are ready.
                running_check_in = await get_running_check_in(contest)
                if running_check_in:
                    time_since_start = current_datetime - running_check_in.started_at
                    if time_since_start.days >= 1:
                        logger.info('Closing out check-in: %s', running_check_in)
                        running_check_in.finished = True
                        await sync_to_async(running_check_in.save, thread_sensitive=True)()
                        channel = bot.get_channel(int(contest.channel_id))
                        await channel.send(f'💪 Check in for {running_check_in.starting} is over 💪')
                else:
                    startable = await get_startable_check_in(contest)
                    if startable is not None:
                        logger.info('Found a startable check-in: %s', startable)
                        await initialize_check_in(startable, bot)
        except Exception:
            logger.exception('Failure during update poll')

        # We don't need to run this loop a lot, so keep this number (relatively) high
        await asyncio.sleep(60)


async def monitor():
    logger.info('Client initializing')
    try:
        intents = discord.Intents.default()
        intents.message_content = True
        bot = WeighbotClient(intents=intents)
        asyncio.create_task(bot.start(settings.BOT_TOKEN))
        await asyncio.sleep(10)
        asyncio.create_task(poll_for_updates(bot))
    except Exception:
        logger.exception('Failed to initialize')
    logger.info('Done initializing')


class Command(BaseCommand):
    def handle(self, *args, **options):
        logger.info('=====> Starting the bot')

        if settings.BOT_TOKEN is None:
            raise ImproperlyConfigured('Missing BOT_TOKEN setting')

        loop = asyncio.get_event_loop()
        t = loop.create_task(monitor())
        try:
            loop.run_forever()
        except KeyboardInterrupt:
            t.cancel()

        logger.info('=====> Closing the bot')
