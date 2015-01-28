# coding: utf-8
from unittest import TestCase
import asyncio
import time

from test.util.server import server
from iob import Crawler
from iob.request import Request, SleepTask
from iob.error import UnknownTaskType


class BasicTestCase(TestCase):
    def setUp(self):
        server.reset()

    def test_simple_task_generator(self):

        class SimpleCrawler(Crawler):
            data = {'count': 0}

            def task_generator(self):
                for x in range(3):
                    yield Request('test', url=server.get_url())

            def handler_test(self, req, res):
                self.data['count'] += 1

        bot = SimpleCrawler()
        bot.run()
        self.assertEquals(3, bot.data['count'])

    def test_not_defined_task_generator(self):

        class SimpleCrawler(Crawler):
            pass

        bot = SimpleCrawler()
        bot.run()

    def test_broken_task_generator(self):
        class SimpleCrawler(Crawler):
            def task_generator(self):
                1/0

        bot = SimpleCrawler()
        self.assertRaises(ZeroDivisionError, bot.run)

    def test_partially_broken_task_generator(self):
        class SimpleCrawler(Crawler):
            def prepare(self):
                self.points = []

            def task_generator(self):
                yield Request('test', url=server.get_url())
                yield SleepTask(0.5)
                1/0

            def handler_test(self, req, res):
                self.points.append('done')

        bot = SimpleCrawler()
        self.assertRaises(ZeroDivisionError, bot.run)
        try:
            bot.run()
        except Exception as ex:
            self.assertEqual(bot.points, ['done'])

    def test_sleep_task_from_task_generator(self):

        class SimpleCrawler(Crawler):
            def prepare(self):
                self.points = []

            def task_generator(self):
                yield Request('test', url=server.get_url())
                yield Request('test', url=server.get_url())

            def handler_test(self, req, res):
                self.points.append(time.time())

        bot = SimpleCrawler()
        bot.run()
        self.assertTrue(2, len(bot.points))
        self.assertTrue(abs(bot.points[0] - bot.points[1]) < 1)

        class SimpleCrawler(Crawler):
            def prepare(self):
                self.points = []

            def task_generator(self):
                yield Request('test', url=server.get_url())
                yield SleepTask(1.1)
                yield Request('test', url=server.get_url())

            def handler_test(self, req, res):
                self.points.append(time.time())

        bot = SimpleCrawler()
        bot.run()
        self.assertTrue(2, len(bot.points))
        self.assertTrue(abs(bot.points[0] - bot.points[1]) > 1)

    def test_unknown_task_type_error(self):
        class SimpleCrawler(Crawler):
            def task_generator(self):
                yield {'message': 'Show must go on!'}

        bot = SimpleCrawler()
        self.assertRaises(UnknownTaskType, bot.run)
