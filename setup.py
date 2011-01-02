from distutils.core import setup
# for python setup.py develop
import setuptools 

setup(
    name='cachetools',
    author='Martin Czygan',
    author_email='martin.czygan@gmail.com',
    url='https://github.com/miku/cachetools',
    version='0.0.1',
    packages=['cachetools',],
    license='BSD',
    long_description=open('README').read(),
)
