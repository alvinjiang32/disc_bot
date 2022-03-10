from pymongo import MongoClient
from src.database_client.database_utils import get_bets
from src.database_client.database_utils import check_bonus
from src.database_client.database_utils import fetch_leaderboard
from src.database_client.database_utils import attempt_transfer
from src.database_client.database_utils import initiate_bet
from src.database_client.database_utils import fetch_balance
from src.database_client.database_utils import initialize_wallet


class DatabaseClient:
    def __init__(self, token, db_name, collection_name):
        self.client = MongoClient(token)
        # TODO update collection in Heroku
        self.database = self.client.get_database(db_name)
        # TODO update database in Heroku
        self.collection = self.database.get_collection(collection_name)

    async def get_all_bets(self, user, msg):
        entry = self.collection.find_one(user.id)
        active_bets = get_bets(entry, self.active_bets_type)
        prev_bets = get_bets(entry, self.prev_bets_type)

        rsp = '__*{}\'s bets*__:\n**Active**:\n{}\n**Previous**:\n{}' \
            .format(user.name, '\n'.join(active_bets), '\n'.join(prev_bets))
        await msg.channel.send(rsp)

    async def add_bonus(self, user, msg):
        entry = self.collection.find_one(user.id)
        if not entry:
            return

        rsp = check_bonus(entry, user, self.collection)
        await msg.channel.send(rsp)

    async def get_leaderboard(self, user, msg):
        rsp = 'Rankings\n\n\n' + fetch_leaderboard(self.collection).join()
        await msg.channel.send(rsp)

    async def transfer_to(self, user, msg):
        sender = self.collection.find_one(user.id)
        args = msg.content.split()
        if len(args) != 3:
            return
        else:
            res = attempt_transfer(args, self.collection, sender, user)

        (await msg.channel.send(res)) if res else None

    async def create_bet(self, user, msg):
        res = initiate_bet(user, msg, self.collection)
        (await msg.channel.send(res)) if res else None

    async def get_balance(self, user, msg):
        res = fetch_balance(user, self.collection)
        await msg.channel.send(res) if res else None

    async def create_wallet(self, user, msg):
        res = initialize_wallet(user, self.collection)
        await msg.channel.send(res)

    async def validate_bet(self, user, msg):
        await get_bets(user, msg)
        await msg.channel.send("**Enter the number of the bet that you have "
                               "won**")

    async def check_bets(self):
        pass

    @property
    def active_bets_type(self):
        return 'active_bets'

    @property
    def prev_bets_type(self):
        return 'prev_bets'
