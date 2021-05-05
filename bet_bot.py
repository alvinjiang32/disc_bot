import discord
import os
import sqlite3
import atexit
from dotenv import load_dotenv

client = discord.Client()
load_dotenv()

@client.event
async def on_connect():
    print('Successfully Connected')

@client.event
async def on_message(msg):
    if msg.author == client.user:
        return

    # format: !bet {$$$$$} {Bet condition} => Return msg if bet is successful
    if msg.content.startswith('!bet'):
        args = msg.content.split()
        print(args)

        if len(args) != 3:
            return
        else:
            print(args)
            amt = args[1]
            bet = args[2]

            # Check if balance > bet
            balance = ...

            if amt > balance:
                await msg.channel.send(
                    'Insufficient Fund: {}'.format(balance))
            else:
                await msg.channel.send('Your bet for {} currency has '
                                       'successfully been placed: {}'
                                       .format(amt, bet))
                # subtract funds from user, store bet

    # format: !balance => returns users balance
    if msg.content == '!balance':
        user = hash(msg.author)
        # connect to database
        # query database using hash

        res = ...
        # return balance to discord channel
        await msg.channel.send()

    if msg.content.startswith('!transfer'):
        sender = hash(msg.author)

        # get next 2 args

        # check if first arg is valid user
        receivee = ...
        # check if second arg is valid int
        transfer_amt = ...
        # check if balance of sender is > transfer amt... DB query

        # return true if valid amt, false if neg balance

    if msg.content.startswith('!bonus'):
        # claim daily login bonus
        pass

def create_connection(db_file):
    """
        Creates connection to database specified in argument

        :param db_file: (String) DB file name to connect to
        :return: Connection obj or None
    """
    conn = None
    try:
        conn = sqlite3.connect(db_file)

    except sqlite3.Error as err:
        print(err)

    return conn


connection = create_connection(os.getenv('DB'))
if not connection:
    print('Connection failed to Database: {}'.format())
    exit()

client.run(os.getenv('TOKEN'))

@atexit.register
def close_connection():
    print('Terminating Connection...\nSaving Changes...')
    connection.close()

