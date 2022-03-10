from setuptools import setup, find_packages
import pathlib

here = pathlib.Path(__file__).parent.resolve()

long_description = (here / 'README.md').read_text(encoding='utf-8')

setup(
    name='DiscordBettingBot',
    version='0.0.1',
    description='Discord bot used to simulate a betting system',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/alvinjiang32/disc_bot',
    author='Alvin Jiang',
    keywords='discordbot, bot'
)
