from __future__ import with_statement
import os, hashlib, functools
import cPickle as pickle
import sys

from cachetools import cache_directory

class pickled(object):
    """Decorator that caches a function's return value each time it is called.
    If called later with the same arguments, the cached value is returned, and
    not re-evaluated. Pickled version.
    """
    def __init__(self, func):
        self.func = func
        self.cache_dir = cache_directory
        if not os.path.exists(self.cache_dir):
            os.mkdir(self.cache_dir)
    
    def cache_filepath(self, *args):
        """ Get the cached file's path. Path is assembled from
        the wrapped function's name and its positions arguments, e.g.
        
            add:1:1
            
        for a function call like
        
            add(1, 1)
        
        The signature/call string is sha1'ed, then sharded by the first two
        characters of the resulting hexdigest.
        This method will create the necessary directories as needed.
        
        """
        sha1 = hashlib.sha1()
        sha1.update("%s:%s" % (self.func.__name__, 
            ':'.join([ str(x) for x in args])))
        filename = sha1.hexdigest()
        shard = filename[:2]
        shard_path = os.path.join(self.cache_dir, shard)
        if not os.path.exists(shard_path):
            os.mkdir(shard_path)
        cache_file = os.path.join(shard_path, filename)
        return cache_file
        
    def __call__(self, *args):
        cache_file = self.cache_filepath(args)
        try:
            with open(cache_file, 'rb') as handle:
                return pickle.load(handle)
        except EOFError:
            value = self.func(*args)
            try:
                with open(cache_file, 'wb') as handle:
                    pickle.dump(value, handle)
            except Exception, exc:
                print >> sys.stderr, '[E] %s' % exc
            return value
            
        except IOError:
            value = self.func(*args)
            with open(cache_file, 'wb') as handle:
                pickle.dump(value, handle)
            return value

        except TypeError:
            # uncachable -- for instance, passing a list as an argument.
            # Better to not cache than to blow up entirely.
            return self.func(*args)

    def __repr__(self):
        """Return the function's docstring."""
        return self.func.__doc__

    def __get__(self, obj, objtype):
        """Support instance methods."""
        return functools.partial(self.__call__, obj)

class memoized(object):
    """Decorator that caches a function's return value each time it is called.
    If called later with the same arguments, the cached value is returned, and
    not re-evaluated.
    """
    def __init__(self, func):
        self.func = func
        self.cache = {}

    def __call__(self, *args):
        try:
            return self.cache[args]
        except KeyError:
            value = self.func(*args)
            self.cache[args] = value
            return value
        except TypeError:
            # uncachable -- for instance, passing a list as an argument.
            # Better to not cache than to blow up entirely.
            return self.func(*args)

    def __repr__(self):
        """Return the function's docstring."""
        return self.func.__doc__

    def __get__(self, obj, objtype):
        """Support instance methods."""
        return functools.partial(self.__call__, obj)

