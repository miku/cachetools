# -*- coding: utf-8 -*-
import os

cache_directory = os.path.join(os.path.expanduser("~"), ".cachetools")

from decorators import pickled, memoized
from url import URLCache
