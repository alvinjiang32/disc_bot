import discord
import os
import atexit
import datetime
import asyncio
from threading import Thread
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

    async def on_connect(self):
        print('Connected to Discord')

    async def on_message(self, msg):
        if msg.author == self.user:
            return

        user = msg.author

        if msg.content.lower() == '!create wallet':
            entry = self.collection.find_one({'_id': user.id})
            if entry:
                res = '**wallet already exists**!'
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

        # format: !bet {$$$$$} {DURATION in hours} {BET}
        if msg.content.startswith('!bet'):
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
                            "$push": {"active_bets": {bet:
                                datetime.datetime.utcnow()
                                + datetime.timedelta(hours=duration)}},
                            "$set": {"balance": balance - amt}
                        })
                    res = '**Your bet has been placed**:' \
                          '\n{}\n{} Trobucks'.format(amt, bet)
            await msg.channel.send(res)

        # format: !balance
        if msg.content.lower() == '!balance':
            balance = None

            # query database using hash
            query = self.collection.find_one(user.id)
            if query:
                balance = query['balance']
                res = "**{}'s balance**: {} Trobucks".format(user.name,
                                                         balance)
                # return balance to discord channel
                await msg.channel.send(res)

        # format: !transfer {AMOUNT} {RECEIVER_NAME}
        if msg.content.startswith('!transfer'):
            # get next 2 args
            sender = self.collection.find_one(user.id)
            args = msg.content.split()
            if len(args) != 3:
                return
            else:
                try:
                    amt = int(args[1])
                except ValueError:
                    return

                rcvr = ''.join(args[2:])
                # check if first arg is valid user
                receiver = self.collection.find_one({"username": rcvr})
                if not receiver:
                    return
                # check if balance of sender is > transfer amt... DB query
                if sender['balance'] < amt:
                    res = '**Insufficient Funds**: {}'.format(sender[
                                                                  'balance'])
                else:
                    self.collection.update_one(receiver,
                           {
                               '$set': {'balance': receiver['balance'] + amt}
                           })
                    self.collection.update_one(sender,
                        {
                            '$set': {'balance': sender['balance'] - amt}
                        })

                    sender = self.collection.find_one(user.id)
                    receiver = self.collection.find_one({"username": rcvr})
                    res = '**Transfer Successful!**\n\n{}\'s balance: {}\n{' \
                          '}\'s balance: {}'.format(sender['username'], sender[
                        'balance'], receiver['username'], receiver['balance'])
            # return true if valid amt, false if neg balance
            await msg.channel.send(res)

        # format: !leaderboards
        if msg.content.lower == '!leaderboards':
            ldrs = ['{}. {}: {}'.format(i, user['username'], user['balance'])
                    for i, user in enumerate(self.collection.find().sort(
                        'balance', pymongo.DESCENDING), 1)]

            await msg.channel.send('Rankings\n\n' + '\n'.join(ldrs))

        # format: !bonus
        if msg.content.lower() == '!bonus':
            entry = self.collection.find_one(user.id)
            if not entry:
                return

            prev = entry['last_bonus']
            now = datetime.datetime.utcnow()
            if now - prev > datetime.timedelta(hours=24):
                self.collection.update_one(entry,
                    {
                        '$set': {'balance': entry['balance'] + 10,
                        'last_bonus': datetime.datetime.utcnow()}
                    })

                entry = self.collection.find_one(user.id)
                rsp = '{} updated balance: {} Trobucks'.\
                    format(entry['username'], entry['balance'])
            else:
                diff = str(datetime.timedelta(hours=24) - (now - prev))
                units = diff.split(':')

                rsp = '**{} hrs, {} minutes, and {} seconds** until your ' \
                      'bonus is available again'.format(units[0], units[1],
                                                        units[2])
            await msg.channel.send(rsp)

        # format: !check bets
        if msg.content.lower() == '!check bets':
            entry = self.collection.find_one(user.id)
            active_bets = [bet for pair in entry['active_bets'] for bet in
                           pair]
            prev_bets = [bet for pair in entry['prev_bets'] for bet in pair]

            rsp = '__*{}\'s bets*__:\n\n**Active**:\n{' \
                  '}\n\n**Previous**:\n\n{}'\
                .format(user.name, '\n'.join(active_bets), '\n'.join(
                 prev_bets))
            await msg.channel.send(rsp)

        # format: !help
        if msg.content.lower() == '!help':
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

    async def check_bets(self):
        pass

@atexit.register
def close_connection():
    print('Terminating Connection...')


if __name__ == '__main__':
    bot = BettingBot()
