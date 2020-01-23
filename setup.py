import os

from setuptools import setup, find_packages

HERE = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(HERE, 'README.md')) as f:
    README = f.read()

setup(
    name='Via 3',
    description='Hypothesis Proxy Application',
    long_description=README,
    url='https://github.com/hypothesis/lms',
    packages=find_packages(),
    include_package_data=True,
)
