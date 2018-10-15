
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
import gov
import app

setup(
    name="gov-zakupki-crawler",
    version=gov.__version__,
    packages=find_packages(exclude=['tests']),
    author="Alexander Ruzhnikov",
    author_email="ruzhnikov85@gmail.com",
    license="MIT",
    python_requires='>=3.7.0',
    install_requires=["asyncio"],
    description="Crawler of resources from ftp.zakupki.gov.ru",
    entry_points={
        "console_scripts": [
            "gov_crawler=app:run"
        ]
    },
    long_description="""..."""
)
