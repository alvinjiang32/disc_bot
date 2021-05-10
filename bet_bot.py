import discord
import os
import atexit
import datetime
import asyncio
from threading import Thread
import threading
import pymongo
from pymongo import MongoClient
from dotenv import load_dotenv


class BettingBot(discord.Client):

    def __init__(self):
        discord.Client.__init__(self)
        load_dotenv()
        self.mdb_client = MongoClient(os.getenv('MDB_TOKEN'))
        self.db = self.mdb_client.test_disc
        self.collection = self.db.test_collection

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
            await self.create_wallet(user, msg)

        # format: !bet {$$$$$} {DURATION in hours} {BET}
        elif msg.content.startswith('!bet'):
            await self.create_bet(user, msg)

        # format: !balance
        elif msg.content.lower() == '!balance':
            await self.get_balance(user, msg)

        # format: !transfer {AMOUNT} {RECEIVER_NAME}
        elif msg.content.startswith('!transfer'):
            await self.transfer_to(user, msg)

        # format: !leaderboards
        elif msg.content.lower == '!leaderboards':
            await self.get_leaderboards(user, msg)

        # format: !bonus
        elif msg.content.lower() == '!bonus':
            await self.add_bonus(user, msg)

        # format: !check bets
        elif msg.content.lower() == '!check bets':
            await self.get_bets(user, msg)

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

    async def get_bets(self, user, msg):
        entry = self.collection.find_one(user.id)
        active_bets = []
        prev_bets = []

        for i, bet in enumerate(entry['active_bets'], 1):
            fmt_msg = '__Bet {}__:```Details: {}\nAmount: {} ' \
                      'Trobucks\nExpiration: {}```'. \
                format(i, bet[0], bet[1], bet[2].
                       strftime("%m/%d/%y @ %I:%M %p"))
            active_bets.append(fmt_msg)

        for i, bet in enumerate(entry['prev_bets'], 1):
            fmt_msg = '__Bet {}__:```Details: {}\nAmount: {} ' \
                      'Trobucks\nExpiration: {}```'. \
                format(i, bet[0], bet[1], bet[2].
                       strftime("%m/%d/%y @ %I:%M %p"))
            active_bets.append(fmt_msg)

        rsp = '__*{}\'s bets*__:\n**Active**:\n{}\n**Previous**:\n{}' \
            .format(user.name, '\n'.join(active_bets), '\n'.join(
             prev_bets))

        await msg.channel.send(rsp)

    async def add_bonus(self, user, msg):
        entry = self.collection.find_one(user.id)
        if not entry:
            return

        prev = entry['last_bonus']
        now = datetime.datetime.utcnow()
        if now - prev > datetime.timedelta(hours=24):
            self.collection.update_one(entry,
               {
                   '$set': {'balance': entry[
                                           'balance'] + 10,
                            'last_bonus': datetime.datetime.utcnow()}
               })

            entry = self.collection.find_one(user.id)
            rsp = '```{} updated balance: {} Trobucks```'. \
                format(entry['username'], entry['balance'])
        else:
            diff = str(datetime.timedelta(hours=24) - (now - prev))
            units = diff.split(':')

            rsp = '**{} hrs, {} minutes, and {} seconds** until your ' \
                  'bonus is available again'.format(units[0], units[1],
                                                    units[2])
        await msg.channel.send(rsp)

    async def get_leaderboards(self, user, msg):
        ldrs = ['{}. {}: {}'.format(i, user['username'], user['balance'])
                for i, user in enumerate(self.collection.find().sort(
                'balance', pymongo.DESCENDING), 1)]

        await msg.channel.send('Rankings\n\n' + '\n'.join(ldrs))

    async def transfer_to(self, user, msg):
        sender = self.collection.find_one(user.id)
        args = msg.content.split()
        if len(args) != 3:
            return
        else:
            try:
                amt = int(args[1])
            except ValueError:
                return

            rcvr_name = ''.join(args[2:])
            # check if first arg is valid user
            receiver = self.collection.find_one({"username": rcvr_name})
            if not receiver or amt < 0:
                return
            # check if balance of sender is > transfer amt
            if sender['balance'] < amt:
                res = '**Insufficient Funds**: {}'.format(
                    sender['balance'])
            else:
                self.collection.update_one(receiver, {
                    '$set': {'balance': receiver['balance'] + amt}
                })
                self.collection.update_one(sender, {
                    '$set': {'balance': sender['balance'] - amt}
                })

                sender = self.collection.find_one(user.id)
                receiver = self.collection.find_one({"username":
                                                         rcvr_name})
                res = '**Transfer Successful!**\n```{}\'s balance: {' \
                      '}\n{}\'s balance: {}```'.format(sender['username'],
                                                       sender['balance'],
                                                       receiver['username'],
                                                       receiver['balance'])

        await msg.channel.send(res)

    async def create_bet(self, user, msg):
        args = msg.content.split()

        if len(args) < 4:
            return
        else:
            try:
                amt = int(args[1])
                duration = int(args[2])
                bet = ' '.join(args[3:])
            except ValueError:
                return

            # Check if balance > bet
            entry = self.collection.find_one({'_id': user.id})
            if not entry:
                return

            balance = entry['balance']
            if amt > balance:
                res = '**You\'re too poor bro**: {} trobucks'.format(
                    balance)
            else:
                self.collection.update_one(entry,
                   {
                       "$push": {
                           "active_bets": (bet, amt,
                                           datetime.datetime.utcnow()
                                           + datetime.timedelta(
                                               hours=duration))},
                       "$set": {
                           "balance": balance - amt}
                   })
                res = '**Your bet has been placed**:' \
                      '\n```{} Trobucks\n{}```'.format(amt, bet)
        await msg.channel.send(res)

    async def get_balance(self, user, msg):
        balance = None

        # query database using id
        query = self.collection.find_one(user.id)
        if query:
            balance = query['balance']
            res = "```{}'s balance: {} Trobucks```".format(user.name,
                                                           balance)
            # return balance to discord channel
            await msg.channel.send(res)

    async def create_wallet(self, user, msg):
        entry = self.collection.find_one({'_id': user.id})
        if entry:
            res = '**Wallet Already Exists**!'
        else:
            new_user = {
                "username": ''.join(user.name).lower(),
                # + user.discriminator,
                "alias": user.nick,
                "_id": user.id,
                "balance": 100,
                "active_bets": [],
                "prev_bets": [],
                "last_bonus": datetime.datetime.utcnow()
            }
            self.collection.insert_one(new_user)
            res = "Welcome {}!\n**Your starting balance is 100 " \
                  "Trobucks**" \
                .format(user.name)
        await msg.channel.send(res)

    async def validate_bet(self, user, msg):
        await self.get_bets(user, msg)
        await msg.channel.send("**Enter the number of the bet that you have "
                               "won**")

    async def check_bets(self):
        pass

@atexit.register
def close_connection():
    print('Terminating Connection...')


if __name__ == '__main__':
    bot = BettingBot()
