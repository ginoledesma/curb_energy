import importlib.machinery
import os

from setuptools import setup, find_packages

here = os.path.dirname(os.path.abspath(__file__))
loader = importlib.machinery.SourceFileLoader(
    'curb_energy', os.path.join(here, 'src', 'curb_energy', '__init__.py')
)

install_requires = [
    'aiohttp',
    'certifi',
    'hbmqtt',
    'marshmallow',
    'pytz',
    'sortedcontainers',
    'Sphinx',
]


setup_requires = [
    'pytest_runner',
]

tests_require = install_requires + [
    'coverage',
    'flake8',
    'responses',
    'pylint',
    'pytest',
    'pytest-asyncio',
    'pytest-cov',
    'pytest-flake8',
    'vcrpy',
]


setup(
    name='curb_energy',
    version=loader.load_module().__version__,
    description='A library for working with the Curb REST API',
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved :: Apache Software License",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: Implementation :: CPython",
        "Topic :: Communications",
        "Topic :: System :: Distributed Computing",
        "Topic :: System :: Networking",
    ],
    keywords='curb energy monitoring',
    author="Gino Ledesma",
    author_email="gledesma@gmail.com",
    url="https://github.com/ginoledesma/curb_energy/",
    license="Apache 2.0",
    packages=find_packages('src'),
    package_dir={'': 'src'},
    test_suite="tests",
    include_package_data=True,
    install_requires=install_requires,
    tests_require=tests_require,
    setup_requires=setup_requires,
)
