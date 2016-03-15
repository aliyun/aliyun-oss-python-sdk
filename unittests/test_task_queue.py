# -*- coding: utf-8 -*-

import unittest
import time

from oss2.task_queue import TaskQueue


class TestTaskQueue(unittest.TestCase):
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

    def test_terminate_consumers(self):
        def producer(q):
            q.put(0)

            while q.ok():
                q.put(1)

        def consumer(q):
            while q.ok():
                item = q.get()
                if item == 0:
                    raise RuntimeError("some error")

        q = TaskQueue(producer, [consumer, consumer])

        self.assertRaises(RuntimeError, q.run)


