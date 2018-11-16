# -*- coding: utf-8 -*-

import unittest
import time

from oss2.task_queue import TaskQueue
from functools import partial
from unittests.common import NonlocalObject


class TestTaskQueue(unittest.TestCase):
    def test_basic(self):
        n = 50

        def producer(q):
            for i in range(n):
                q.put(1)

        def consumer(q, total):
            while q.ok():
                value = q.get()
                if value is None:
                    break

                total.var += value

        # one consumer
        total = NonlocalObject(0)
        q = TaskQueue(producer, [partial(consumer, total=total)])
        q.run()

        self.assertEqual(total.var, n)

        # two consumers
        total_1 = NonlocalObject(0)
        total_2 = NonlocalObject(0)
        q = TaskQueue(producer, [partial(consumer, total=total_1), partial(consumer, total=total_2)])
        q.run()

        self.assertEqual(total_1.var + total_2.var, n)

    def test_more_consumers(self):
        n = 10

        def producer(q):
            for i in range(n):
                q.put(1)

        def consumer(q, total):
            while q.ok():
                value = q.get()
                if value is None:
                    break

                total.var += value

        total_list = [NonlocalObject(0) for i in range(n*2)]
        consumer_list = [partial(consumer, total=total) for total in total_list]
        q = TaskQueue(producer, consumer_list)
        q.run()

        result = sum(total.var for total in total_list)
        self.assertEqual(result, n)

    def test_consumer_exception(self):
        def produder(q):
            time.sleep(1)
            q.put(1)

        def consumer(q):
            while q.ok():
                q.get()
                raise RuntimeError("some error")

        q = TaskQueue(produder, [consumer])
        self.assertRaises(RuntimeError, q.run)

    def test_producer_exception(self):
        def producer(q):
            time.sleep(1)
            raise RuntimeError("some error")

        def consumer(q):
            while q.ok():
                if q.get() is None:
                    break

        q = TaskQueue(producer, [consumer])

        self.assertRaises(RuntimeError, q.run)

    def test_early_terminated_consumers(self):
        """Consumers are terminated early, and what producer produces are not consumed."""

        def producer(q):
            time.sleep(1)
            for i in range(4096):
                q.put(1)

        def consumer(q):
            raise RuntimeError("some error")

        q = TaskQueue(producer, [consumer])

        self.assertRaises(RuntimeError, q.run)


if __name__ == '__main__':
    unittest.main()
