# -*- coding: utf-8 -*-

from contextlib import contextmanager
from timeit import default_timer
import time

# source: http://stackoverflow.com/a/30024601/2422367
@contextmanager
def elapsed_timer():
    """
    usage:
        with elapsed_timer() as elapsed:
            ...
            print(elapsed())
    """
    start = default_timer()
    elapser = lambda: default_timer() - start
    yield lambda: elapser()
    end = default_timer()
    elapser = lambda: end-start

