import asyncio
import atexit
import os

import discord
from dotenv import load_dotenv

from src.database_client.database_client import DatabaseClient


class BettingBot(discord.Client):
    def __init__(self):
        discord.Client.__init__(self)
        load_dotenv()
        self.mdb_client = DatabaseClient(os.getenv('MDB_TOKEN'), os.getenv('DEFAULT_DB'), os.getenv('DEFAULT_COLLECTION'))

        self.loop = asyncio.get_event_loop()
        self.loop.create_task(self.start(os.getenv('TOKEN')))
        self.loop.run_forever()

    @staticmethod
    async def on_connect():
        print('Connected to Discord')

    async def on_message(self, msg):
        if msg.author == self.user:
            return

        user = msg.author
        if msg.content.lower() == '!create wallet':
            await self.mdb_client.create_wallet(user, msg)

        # format: !bet {$$$$$} {DURATION in hours} {BET}
        elif msg.content.startswith('!bet'):
            await self.mdb_client.create_bet(user, msg)

        # format: !balance
        elif msg.content.lower() == '!balance':
            await self.mdb_client.get_balance(user, msg)

        # format: !transfer {AMOUNT} {RECEIVER_NAME}
        elif msg.content.startswith('!transfer'):
            await self.mdb_client.transfer_to(user, msg)

        # format: !leaderboards
        elif msg.content.lower == '!leaderboard':
            await self.mdb_client.get_leaderboard(user, msg)

        # format: !bonus
        elif msg.content.lower() == '!bonus':
            await self.mdb_client.add_bonus(user, msg)

        # format: !check bets
        elif msg.content.lower() == '!check bets':
            await self.mdb_client.get_all_bets(user, msg)

        # format: !help
        elif msg.content.lower() == '!help':
            await self.get_commands(msg)

    @staticmethod
    async def get_commands(msg):
        rsp = '**Supported Commands**:\n\n' \
              'To create a wallet\n```!create wallet```\n' \
              'To create a new bet\n```!bet {AMOUNT} {' \
              'DURATION_IN_HOURS} {BET_DETAILS}```\n' \
              'To transfers funds to another user\n```!transfer {' \
              'AMOUNT} {RECEIVERS_DISCORD_NAME}```\n' \
              'To get your balance\n```!balance```\n' \
              'To get your bonus\n```!bonus```\n' \
              'To get the leaderboard rankings\n```!leaderboards```\n'
        await msg.channel.send(rsp)


@atexit.register
def close_connection():
    print('Terminating Connection...')


if __name__ == '__main__':
    bot = BettingBot()
