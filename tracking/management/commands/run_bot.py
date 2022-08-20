import asyncio
import logging
from typing import List

import discord
from django.conf import settings
from django.core.management import BaseCommand

from tracking.bot import WeighbotClient
from tracking.logic import initialize_contest, initialize_check_in, get_startable_check_in
from tracking.models import Contest

logger = logging.getLogger(__name__)


def clean_text(text: str) -> List[str]:
    return text.strip().split(' ')


async def poll_for_updates(bot: 'tracking.bot.WeighbotClient'):
    while True:
        try:
            # Update all our contests
            async for contest in Contest.objects.all():
                # Is this contest un-initialized?
                check_in_count = await contest.check_ins.acount()
                if check_in_count == 0:
                    await initialize_contest(contest)
                # The contest is initialized, check if we need to start the next check-in
                else:
                    logger.info('Contest is waiting for startable check-in: %s', contest)
                    startable = await get_startable_check_in(contest)
                    if startable:
                        logger.info('Found a startable check-in: %s', startable)
                        await initialize_check_in(startable, bot)
        except:
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
    except:
        logger.exception('Failed to initialize')
    logger.info('Done initializing')


class Command(BaseCommand):
    def handle(self, *args, **options):
        logger.info('=====> Starting the bot')

        loop = asyncio.get_event_loop()
        t = loop.create_task(monitor())
        try:
            loop.run_forever()
        except KeyboardInterrupt:
            t.cancel()

        logger.info('=====> Closing the bot')
