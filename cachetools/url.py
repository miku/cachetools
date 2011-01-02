#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
General purpose filesystem URL caching. 
=======================================

Note: We are not backwards-compatible, 
    we need python 2.5+ (hashlib)

Sample usage
------------

from cachetools import URLCache

cache = URLCache() # get a cache instance

page = cache.get("http://www.heise.de")
page, hit = cache.get("http://www.heise.de", hit=True)

Defaults
--------

directory = $HOME/.cachetools
user_agent = 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'
compress = True
invalidate = 604800
debug = False
enabled = True
proxy = None
rotating_user_agent = False
user_agent_list = [
    'Opera/9.0 (Windows NT 5.1; U; en) ',
    'Avant Browser (http://www.avantbrowser.com)',
    'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'
    ]

For more user agents see: cachetools.useragent

Todo
----

$ pylint cachedurl.py
2 R: 58:URLCache: Too many instance attributes (9/7)
3 R: 61:URLCache.__init__: Too many arguments (8/5)
4 R:127:URLCache.get: Too many branches (16/12)

...

Your code has been rated at 9.62/10 (previous run: 9.62/10)

"""

from __future__ import division
from hashlib import sha256
from stat import ST_MTIME
from time import time

import bz2, os, sys, urllib2, random

from cachetools import cache_directory

class CacheFailed(Exception):
    """ General and uninformative Exception.
    """
    def __init__(self, value):
        super(CacheFailed, self).__init__()
        self.value = value
    def __str__(self):
        return repr(self.value)
    
class URLCache(object):
    """ General (optionally) bzip2'd sha256-identified cache repository.
    """
    def __init__(self, directory=cache_directory,
            user_agent='Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)',
            compress=True,
            invalidate=604800,
            debug=False,
            proxy=None,
            rotating_user_agent=False):
            
        start = time()
        
        self.directory = directory
        self.user_agent = user_agent
        self.enabled = True
        self.compress = compress
        self.invalidate = invalidate
        self.debug = debug
        self.proxy = proxy
        self.rotating_user_agent = rotating_user_agent
        
        self.user_agent_list = [
            'Opera/9.0 (Windows NT 5.1; U; en) ',
            'Avant Browser (http://www.avantbrowser.com)',
            'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'
        ]
        
        self.prepare()
        if debug:
            print >> sys.stderr, '[Cache] Cache up: %f' % (time() - start)

    def prepare(self):
        """
        Check, if cache dir exists.
        """
        if not os.path.exists(self.directory):
            try:
                os.makedirs(self.directory)
            except IOError, ioe:
                self.enabled = False
                raise CacheFailed(
                    'CachedURL, could not create cache dir. {0}'.format(ioe))
                
    
    def get_cache_file_dir(self, cache_filename, create=True):
        """
        Returns the subdirectory for the cached file name. 
        We split the sha256 sum of the url up into a 16 char prefix and the rest.
        The 16 chars will form the directory, e.g.
            fee9548909ac73ccbb560e887ab3cbca190cfad80a7b12b2574f96fa223e7e12
        would become
            fe/
        
        so each directory has no more the 2 subdirectories, should be handable by ext3
        """
        _prefix = cache_filename[:2] # [ c for c in cache_filename ][:2]
        _path = _prefix # '/'.join(_prefix)
        _dir = os.path.join(self.directory, _path)
        if not os.path.exists(_dir) and create:
            try:
                os.makedirs(_dir)
            except IOError, ioe:
                raise CacheFailed(
                    'We could not create cache directory {0} {1}'.format(
                        _dir, ioe))
        return _dir
    
    def get(self, url, hit=False):
        """
        Retrieve URL.
        """
        if not self.enabled:
            return
        contents, cache_hit = None, False
        fun = sha256()
        fun.update(url)
        
        hxd = fun.hexdigest()
        if self.compress:
            cache_candidate = os.path.join(
                self.get_cache_file_dir(hxd), '%s.bz2' % hxd)
        else:
            cache_candidate = os.path.join(self.get_cache_file_dir(hxd), hxd)

        try:
            if (os.path.exists(cache_candidate) 
                and self.entry_is_valid(cache_candidate)):
                
                start = time()
                handle = open(cache_candidate, 'r')
                contents = handle.read()
                if self.compress: 
                    contents = bz2.decompress(contents)
                handle.close()
                if self.debug:
                    print >> sys.stderr, \
                        '[Cache] Cache hit: {0} {1} [{2}]'.format(
                            url, cache_candidate, time() - start)
                cache_hit = True
            else:
                start = time()
                req = urllib2.Request(url)
                if not self.proxy == None:
                    proxy_support = urllib2.ProxyHandler(
                        {'http' : self.proxy})
                    opener = urllib2.build_opener(proxy_support)
                    urllib2.install_opener(opener)
                if self.debug:
                    print >> sys.stderr, \
                        '[Cache] Cache: Retrieving {0}'.format(url)
                if self.rotating_user_agent:
                    self.user_agent = random.choice(self.user_agent_list)
                else:
                    self.user_agent = self.user_agent_list[0]
                req.add_header('User-Agent', self.user_agent)
                contents = urllib2.urlopen(req).read()
                handle = open(cache_candidate, 'w')
                if self.compress:
                    handle.write(bz2.compress(contents))
                else:
                    handle.write(contents)
                handle.close()
                if self.debug:
                    print >> sys.stderr, \
                        '[Cache] Cache: Retreived {0} [{1}]'.format(
                            url, time() - start)
            if hit:
                return (contents, cache_hit)
            else:
                return contents
        except Exception, exc:
            raise CacheFailed('Cache Failed: {0}'.format(exc))
    
    def entry_is_valid(self, filename):
        """ Check if file is up to date. 
            See also: cache ``invalidate`` attribute.
        """
        if self.invalidate == 0:
            return True
        return (time() - os.stat(filename)[ST_MTIME]) < self.invalidate

if __name__ == '__main__':
    pass

