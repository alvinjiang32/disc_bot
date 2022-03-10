import datetime
import pymongo


def get_bets(entry, bet_type):
    bets = []
    for i, bet in enumerate(entry[bet_type], 1):
        fmt_msg = '__Bet {}__:```Details: {}\nAmount: {} ' \
                  'Burrys\nExpiration: {}```'. \
            format(i, bet[0], bet[1], bet[2].
                   strftime("%m/%d/%y @ %I:%M %p"))
        bets.append(fmt_msg)

    return bets


def check_bonus(entry, user, collection):
    prev = entry['last_bonus']
    now = datetime.datetime.utcnow()
    if now - prev > datetime.timedelta(hours=24):
        collection.update_one(entry,
                              {'$set': {'balance': entry['balance'] + 10, 'last_bonus': datetime.datetime.utcnow()}})

        entry = collection.find_one(user.id)
        return '```{} updated balance: {} Burrys```'.format(entry['username'], entry['balance'])
    else:
        diff = str(datetime.timedelta(hours=24) - (now - prev))
        units = diff.split(':')

        return '**{} hrs, {} minutes, and {} seconds** until your bonus is available again' \
            .format(units[0], units[1], units[2])


def fetch_leaderboard(collection):
    return ['{}. {}: {}'.format(i, user['username'], user['balance'])
            for i, user in enumerate(collection.find().sort('balance', pymongo.DESCENDING), 1)]


def attempt_transfer(args, collection, sender, user):
    try:
        amt = int(args[1])
    except ValueError:
        return

    rcvr_name = ''.join(args[2:])
    # check if first arg is valid user
    receiver = collection.find_one({"username": rcvr_name})
    if not receiver or amt < 0:
        return
    # check if balance of sender is > transfer amt
    if sender['balance'] < amt:
        return '**Insufficient Funds**: {}'.format(sender['balance'])
    else:
        collection.update_one(receiver, {'$set': {'balance': receiver['balance'] + amt}})
        collection.update_one(sender, {'$set': {'balance': sender['balance'] - amt}})

        sender = collection.find_one(user.id)
        receiver = collection.find_one({"username": rcvr_name})

        return "**Transfer Successful!**\n```{}\'s balance: {''}\n{}\'s balance: {}```".format(
            sender['username'], sender['balance'], receiver['username'], receiver['balance'])


def initiate_bet(user, msg, collection):
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
        entry = collection.find_one({'_id': user.id})
        if not entry:
            return

        balance = entry['balance']
        if amt > balance:
            return '**You\'re too poor bro**: {} Burrys'.format(
                balance)
        else:
            collection.update_one(entry,
                                  {
                                      "$push": {"active_bets": (
                                      bet, amt, datetime.datetime.utcnow() + datetime.timedelta(hours=duration))},
                                      "$set": {"balance": balance - amt}
                                  })
            return '**Your bet has been placed**:\n```{} Burrys\n{}```'.format(amt, bet)


def fetch_balance(user, collection):
    # query database using id
    query = collection.find_one(user.id)
    if query:
        balance = query['balance']
        return "```{}'s balance: {} Burrys```".format(user.name, balance)


def initialize_wallet(user, collection):
    entry = collection.find_one({'_id': user.id})
    if entry:
        return '**Wallet Already Exists**!'
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
        collection.insert_one(new_user)
        return "Welcome {}!\n**Your starting balance is 100 Burrys**".format(user.name)
