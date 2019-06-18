
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
import gov

setup(
    name="gov-purchases-crawler",
    version=gov.__version__,
    packages=find_packages(exclude=['tests']),
    author="Alexander Ruzhnikov",
    author_email="ruzhnikov85@gmail.com",
    license="MIT",
    python_requires='>=3.6.0',
    install_requires=["lxml", "psycopg2", "psycopg2-binary", "SQLAlchemy"],
    setup_requires=['pytest-runner'],
    tests_require=["pytest"],
    description="Crawler of resources from ftp.zakupki.gov.ru",
    url='https://github.com/ruzhnikov/gov-purchases-crawler',
    entry_points={
        "console_scripts": [
            "gov-purchases=gov.app:run"
        ]
    },
    long_description="""..."""
)
