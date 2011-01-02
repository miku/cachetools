# -*- coding: utf-8 -*-

import cachetools
import cPickle as pickle
import os, sys, time
import unittest

MSG_PERF = """
The uncached computation is faster than the cached one. This
shouldn't happen, but if you're sure, you can safely ignore a
failure an AssertionError in this test. Artificial delay
was set to %(sleep_time)s seconds.
"""

class PickledTestCase(unittest.TestCase):

    def test_basic(self):
        def crash_dummy_fun(a, b, c):
            return a + b + c
        result = crash_dummy_fun(1, 2, 3)
        self.assertEqual(6, result)
    
    def test_directory_creation(self):
        def crash_dummy_fun(a, b, c):
            return a + b + c
        path = cachetools.pickled(crash_dummy_fun).cache_filepath(1, 2, 3)
        assert os.path.exists(os.path.dirname(path))
        assert path.startswith(cachetools.cache_directory)

    def test_performance(self):
        sleep_time = 0.01
        def crash_dummy_fun(a, b, c):
            time.sleep(sleep_time)
            return a + b + c
            
        # below is the sha1 sum of 'crash_dummy_fun' with args (1, 2, 1)
        path = os.path.join(cachetools.cache_directory, 'c0', 
            'c01ca90602c7c0ebd873ce5d19b075280bb8aa33')
        if os.path.exists(path):
            os.remove(path)
        
        crash_dummy_fun = cachetools.pickled(crash_dummy_fun)
        
        start = time.time()
        crash_dummy_fun(1, 2, 1)
        stop = time.time()
        uncached_time = stop - start

        assert os.path.exists(path)

        start = time.time()
        crash_dummy_fun(1, 2, 1)
        stop = time.time()
        cached_time = stop - start

        assert uncached_time > cached_time, MSG_PERF % locals()

class MemoizedTestCase(unittest.TestCase):
    pass
    