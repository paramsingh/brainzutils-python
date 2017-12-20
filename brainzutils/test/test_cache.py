# -*- coding: utf-8 -*-
# pylint: disable=protected-access

import datetime
import os
import redis
import unittest

from brainzutils import cache


class CacheTestCase(unittest.TestCase):
    """Testing our custom wrapper for redis."""
    host = os.environ.get("REDIS_HOST", "localhost")
    port = 6379
    namespace = "NS_TEST"

    def setUp(self):
        cache.init(
            host=self.host,
            port=self.port,
            namespace=self.namespace,
        )
        # Making sure there are no items in cache before we run each test
        cache.flush_all()

    def tearDown(self):
        cache.delete_ns_versions_dir()

    def test_no_init(self):
        cache._r = None
        with self.assertRaises(RuntimeError):
            cache.set("test", "testing")
        with self.assertRaises(RuntimeError):
            cache.get("test")

    def test_single(self):
        self.assertTrue(cache.set("test2", "Hello!"))
        self.assertEqual(cache.get("test2"), "Hello!")

    def test_single_no_encode(self):
        self.assertTrue(cache.set("no encode", 1, encode=False))
        self.assertEqual(cache.get("no encode", decode=False), b"1")

    def test_single_with_namespace(self):
        self.assertTrue(cache.set("test", 42, namespace="testing"))
        self.assertEqual(cache.get("test", namespace="testing"), 42)

    def test_single_fancy(self):
        self.assertTrue(cache.set("test3", u"Привет!"))
        self.assertEqual(cache.get("test3"), u"Привет!")

    def test_single_dict(self):
        dictionary = {
            "fancy": "yeah",
            "wow": 11,
        }
        self.assertTrue(cache.set('some_dict', dictionary))
        self.assertEqual(cache.get('some_dict'), dictionary)

    def test_single_dict_fancy(self):
        dictionary = {
            "fancy": u"Да",
            "тест": 11,
        }
        cache.set('some_dict', dictionary)
        self.assertEqual(cache.get('some_dict'), dictionary)

    def test_datetime(self):
        self.assertTrue(cache.set('some_time', datetime.datetime.now()))
        self.assertEqual(type(cache.get('some_time')), datetime.datetime)

        dictionary = {
            "id": 1,
            "created": datetime.datetime.now(),
        }
        self.assertTrue(cache.set('some_other_time', dictionary))
        self.assertEqual(cache.get('some_other_time'), dictionary)

    def test_delete(self):
        key = "testing"
        self.assertTrue(cache.set(key, u"Пример"))
        self.assertEqual(cache.get(key), u"Пример")
        self.assertEqual(cache.delete(key), 1)
        self.assertIsNone(cache.get(key))

    def test_delete_with_namespace(self):
        key = "testing"
        namespace = "spaaaaaaace"
        self.assertTrue(cache.set(key, u"Пример", namespace=namespace))
        self.assertEqual(cache.get(key, namespace=namespace), u"Пример")
        self.assertEqual(cache.delete(key, namespace=namespace), 1)
        self.assertIsNone(cache.get(key, namespace=namespace))

    def test_many(self):
        # With namespace
        mapping = {
            "test1": "Hello",
            "test2": "there",
        }
        self.assertTrue(cache.set_many(mapping, namespace="testing-1"))
        self.assertEqual(cache.get_many(list(mapping.keys()), namespace="testing-1"), mapping)

        # With another namespace
        test = cache.get_many(list(mapping.keys()), namespace="testing-2")
        for key, val in test.items():
            self.assertIn(key, mapping)
            self.assertIsNone(val)

        # Without a namespace
        mapping = {
            "test1": "What's",
            "test2": "good",
        }
        self.assertTrue(cache.set_many(mapping))
        self.assertEqual(cache.get_many(list(mapping.keys())), mapping)

    def test_invalidate_namespace(self):
        namespace = "test"
        self.assertEqual(cache.invalidate_namespace(namespace), 1)
        self.assertEqual(cache.invalidate_namespace(namespace), 2)

        with self.assertRaises(ValueError):
            cache.invalidate_namespace(u"Тест")
        with self.assertRaises(ValueError):
            cache.invalidate_namespace("Hello!")

    def test_namespace_version(self):
        name = "test"
        self.assertIsNone(cache.get_namespace_version(name))
        self.assertEqual(cache.invalidate_namespace(name), 1)
        self.assertEqual(cache.get_namespace_version(name), 1)
        self.assertEqual(cache.invalidate_namespace(name), 2)
        self.assertEqual(cache.get_namespace_version(name), 2)

        with self.assertRaises(ValueError):
            cache.get_namespace_version(u"Тест")
        with self.assertRaises(ValueError):
            cache.get_namespace_version("Hello!")

    def test_increment(self):
        cache.set("a", 1, encode=False)
        self.assertEqual(cache.increment("a"), 2)

    def test_increment_invalid_value(self):
        cache.set("a", "not a number")
        with self.assertRaises(redis.exceptions.ResponseError):
            cache.increment("a")

    def test_max_key_length(self):
        self.assertIsNone(cache.get_max_key_length())
        cache.set("1234", "val")
        self.assertEqual(cache.get_max_key_length(), 4)
        cache.set("12345", "val1")
        self.assertEqual(cache.get_max_key_length(), 5)
        cache.set("1234", "val2")
        self.assertEqual(cache.get_max_key_length(), 5)
        cache.set("123456", "val1", namespace="test_namespace")
        self.assertEqual(cache.get_max_key_length(namespace="test_namespace"), 6)
        self.assertEqual(cache.get_max_key_length(), 5)
