import datetime
import random
from unittest.mock import Mock, AsyncMock

from django.test import TestCase
from django.utils import timezone

from tracking.logic import initialize_contest, get_startable_check_in, initialize_check_in
from tracking.models import Contest, CheckIn


def init_happy_path_contest(period: int, num_check_ins: int):
    start_date = timezone.now().date()
    interval = datetime.timedelta(days=period)
    end_date = start_date + (interval * num_check_ins)
    return Contest.objects.create(
        name='happy',
        starting=start_date,
        check_in_period=7,
        final_check_in=end_date,
        channel_id='123456789'
    )


class ContestTestCase(TestCase):
    def setUp(self) -> None:
        self.num_check_ins = 10
        self.contest = init_happy_path_contest(period=7, num_check_ins=self.num_check_ins)

    async def test_contest_initialization(self):
        await initialize_contest(self.contest)
        self.assertEqual(await self.contest.check_ins.acount(), self.num_check_ins)
        all_check_ins = [check_in async for check_in in self.contest.check_ins.select_related('previous').order_by('starting')]
        previous = all_check_ins[0]
        for check_in in all_check_ins[1:]:
            self.assertEqual(previous.starting, check_in.previous.starting)
            self.assertLess(previous.starting, check_in.starting)
            previous = check_in


class CheckInQueryTestCase(TestCase):
    def setUp(self) -> None:
        self.num_check_ins = 3
        self.contest = init_happy_path_contest(period=7, num_check_ins=self.num_check_ins)

    async def test_check_in_startable_query(self):
        await initialize_contest(self.contest)
        check_in: CheckIn = await get_startable_check_in(self.contest)
        self.assertIsNotNone(check_in)
        today = timezone.now().date()
        self.assertEqual(check_in.starting, today)


class CheckInInitializeTestCase(TestCase):
    def setUp(self) -> None:
        self.num_check_ins = 3
        self.contest = init_happy_path_contest(period=7, num_check_ins=self.num_check_ins)

    async def test_check_in_init(self):
        await initialize_contest(self.contest)
        check_in: CheckIn = await get_startable_check_in(self.contest)
        self.assertIsNotNone(check_in)
        bot = Mock()
        channel = AsyncMock()
        thread = AsyncMock()
        message = AsyncMock()
        channel.send = AsyncMock(return_value=message)
        channel.create_thread = AsyncMock(return_value=thread)
        thread.id = 1000 + random.random() * 1000
        bot.get_channel = Mock(return_value=channel)
        await initialize_check_in(check_in, bot)
        self.assertEqual(
            channel.create_thread.call_args[1]['name'],
            f'Check-in'
        )
        self.assertEqual(
            thread.send.call_args[0][0],
            'Send a message with your weight in pounds, and any images you want to share (all in the same message)'
        )
        self.assertEqual(
            check_in.thread_id,
            thread.id
        )
