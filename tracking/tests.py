import datetime
import random
from unittest.mock import Mock, AsyncMock

from django.test import TestCase
from django.utils import timezone

from tracking.logic import initialize_contest, get_startable_check_in, initialize_check_in, \
    get_weight_from_check_in_text
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
        self.num_check_ins = 3
        self.contest = init_happy_path_contest(period=7, num_check_ins=self.num_check_ins)

    async def test_contest_initialization(self):
        await initialize_contest(self.contest)
        self.assertEqual(await self.contest.check_ins.acount(), self.num_check_ins)


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


class ParseWeightTestCase(TestCase):
    def test_easy_no_unit(self):
        init_weight = 191.1
        easy_no_unit = str(init_weight)
        results = get_weight_from_check_in_text(easy_no_unit)
        weight, unit = results[0]
        self.assertEqual(init_weight, weight)
        self.assertEqual('', unit)

    def test_easy_with_unit(self):
        init_weight = 191.1
        easy_with_unit = f'{init_weight}lbs'
        results = get_weight_from_check_in_text(easy_with_unit)
        weight, unit = results[0]
        self.assertEqual(init_weight, weight)
        self.assertEqual('lbs', unit)

    def test_multi_same_units(self):
        weights = (191.1, 89, 901)
        weight_str = ' '.join(map(lambda x: f'{x}lbs', weights))
        results = get_weight_from_check_in_text(weight_str)
        self.assertEqual(len(weights), len(results))
        for idx, weight in enumerate(weights):
            self.assertEqual(weight, results[idx][0])
            self.assertEqual('lbs', results[idx][1])

    def test_multi_mixed_units(self):
        weights = (191.1, 89, 901)
        units = ('lbs', '', 'kg')
        weight_str = ' '.join(map(lambda x: f'{x[0]}{x[1]}', zip(weights, units)))
        results = get_weight_from_check_in_text(weight_str)
        self.assertEqual(len(weights), len(results))
        for idx, weight in enumerate(weights):
            self.assertEqual(weight, results[idx][0])
            self.assertEqual(units[idx], results[idx][1])

    def test_multi_mixed_units(self):
        examples = (
            ('I weigh 181lbs', [(181.0, 'lbs')]),
            ('All 92kg of me is ready', [(92.0, 'kg')]),
            (
                'I have four steaks weighing 102.lbs, 20kg, 93.985 lbs. Oh yeah, and one that weighs 84.323432 lbs.',
                [(102.0, 'lbs'), (20.0, 'kg'), (93.985, 'lbs'), (84.323432, 'lbs')]
            )
        )
        for example, expected in examples:
            results = get_weight_from_check_in_text(example)
            self.assertEqual(len(expected), len(results))
            for idx, (weight, unit) in enumerate(expected):
                self.assertEqual(weight, results[idx][0])
                self.assertEqual(unit, results[idx][1])
