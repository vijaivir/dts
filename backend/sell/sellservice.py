from flask import Flask, request
from pymongo import MongoClient
import xml.etree.ElementTree as ET
import xml.dom.minidom
import time
import requests

# container name for mongo db
client = MongoClient("mongodb://mongo_database", 27017)

db = client.user_database
# Create two collections (user_table, transaction_table)
user_table = db.user_table
transaction_table = db.transaction_table

app = Flask(__name__)


@app.route("/quote", methods=["POST"])
def get_quote():
    return 10.0
    quote_price = requests.get(
        'http://fe26-2604-3d08-2679-2000-c58a-51ec-8599-b312.ngrok.io/quote')
    res = quote_price.json()
    price = res['price']
    return price


@app.route("/sell", methods=["POST"])
def sell():
    data = request.json
    # check if account exists
    if not account_exists(data['username']):
        return str(new_transaction(data, error="The specified user does not exist."))

    filter = {"username": data['username']}
    user_stocks = user_table.find_one(filter)['stocks']
    # check if owned stock is >= amount being sold
    valid_transaction = False
    for x in user_stocks:
        if (x['sym'] == data['sym']) and (float(x['amount']) > float(data['amount'])):
            valid_transaction = True
    if valid_transaction:
        # add the SELL transaction to the user table (new_transaction() auto adds to transaction_table)
        user_table.update_one(
            filter, {"$push": {"transactions": new_transaction(data)}})
        return 'Added to transactions. 60 seconds to COMMIT'
    # else create an error transaction for the transaction_table
    return str(new_transaction(data, error="Insufficient stock amount."))


@app.route("/commit_sell", methods=["POST"])
def commit_sell():
    data = request.json

    # check if account exists
    if not account_exists(data['username']):
        return str(new_transaction(data, error="The specified user does not exist."))

    # get the most recent transaction with the pending flag
    timestamp = time.time()
    recent_tx = recent_transaction(data['username'], "SELL", timestamp)

    if len(recent_tx) == 0:
        # no recent sell transactions found, create an error transaction for the transaction_table
        return str(new_transaction(data, error="No recent SELL transactions."))
    else:
        filter = {"username": data['username']}
        stock = recent_tx['sym']
        price = recent_tx['amount']
        txNum = recent_tx['transactionNum']

        # subtract stock amount
        stock_filter = {"username": data['username'], "stocks.sym": stock}
        amount_owned = user_table.find_one(stock_filter, {"stocks.$": 1})[
            'stocks'][0]['amount']
        user_table.update_one(
            stock_filter, {"$set": {"stocks.$.amount": float(amount_owned) - float(price)}})

        # add to user funds
        balance = user_table.find_one(filter)['funds']
        user_table.update_one(
            filter, {"$set": {"funds": float(price) + float(balance)}})

        # set pending flag to complete
        user_table.update_one(
            {"username": data['username'],
                "transactions.transactionNum": txNum},
            {"$set": {"transactions.$.flag": "complete"}}
        )

        # add the COMMIT_SELL transaction to the user table (new_transaction() auto adds to transaction_table)
        user_table.update_one(
            filter, {"$push": {"transactions": new_transaction(data)}})

        return 'Successfully committed.'


@app.route("/cancel_sell", methods=["POST"])
def cancel_sell():
    data = request.json

    # check if account exists
    if not account_exists(data['username']):
        return str(new_transaction(data, error="The specified user does not exist."))

    # get the most recent transaction with the pending flag
    timestamp = time.time()
    recent_tx = recent_transaction(data['username'], "SELL", timestamp)

    if len(recent_tx) == 0:
        # no recent sell transactions found, create an error transaction for the transaction_table
        return str(new_transaction(data, error="No recent SELL transactions."))
    else:
        filter = {"username": data['username']}
        txNum = recent_tx['transactionNum']

        # set pending flag to cancelled
        user_table.update_one(
            {"username": data['username'],
                "transactions.transactionNum": txNum},
            {"$set": {"transactions.$.flag": "cancelled"}}
        )

        # add the CANCEL_SELL transaction to the user table (new_transaction() auto adds to transaction_table)
        user_table.update_one(
            filter, {"$push": {"transactions": new_transaction(data)}})

        return 'Successfully cancelled.'

#TODO
@app.route("/set_sell_amount", methods=["POST"])
def set_sell_amount():
    data = request.json
    filter = {'username': data['username']}

    if not account_exists(data['username']):
        new_transaction(data, error="The specified user does not exist.")

    # check if the user has the amount of stock
    valid_stock = user_table.find_one(
        {'username': data['username'], 'stocks.sym': data['sym'], 'stocks.amount': {'$gte': data['amount']}})

    if not valid_stock:
        new_transaction(data, error="Not enough stock.")
        return "Not enough stock owned to SET_SELL_AMOUNT"

    # remove amount from the stock

    # add to reserved sell
    user_table.update_one(filter, {"$push": {"transactions": new_transaction(data),
                                             "reserved_sell": {'sym': data['sym'], 'amount': data['amount']}}})
    return 'successfully set sell amount'


#TODO
@app.route("/set_sell_trigger", methods=["POST"])
def set_sell_trigger():
    data = request.json
    filter = {'username': data['username']}

    if not account_exists(data['username']):
        new_transaction(data, error="The specified user does not exist.")

    # check if the sell amount has been set in reserved_sell[]
    valid_trigger = user_table.find_one(
        {'username': data['username'], 'reserved_sell.sym': data['sym']})

    if not valid_trigger:
        new_transaction(data, error="Set sell amount first.")
        return "Set sell amount first."

    user_table.update_one({'username': data['username'], 'reserved_sell.sym': data['sym']}, {
                          '$set': {'reserved_sell.$.trigger': data['amount']}})
    return 'successfully set sell trigger'


#TODO
@app.route("/cancel_set_sell", methods=["POST"])
def cancel_set_sell():
    data = request.json
    new_transaction(data)
    return 'successfully cancelled'


def new_transaction(data, **atr):
    cmd = data['cmd']

    # default attributes
    tx = {
        "timestamp": time.time(),
        "transactionNum": data['trxNum'],
        "command": cmd,
        "username": data['username'],
    }

    if "error" in atr:
        tx["type"] = "errorEvent"
        tx["server"] = "TS1"
        tx['error'] = atr["error"]
        transaction_table.insert_one(tx)
        return tx

    if cmd == "ADD":
        tx["type"] = "accountTransaction"
        tx['server'] = "TS1"
        tx["amount"] = data['amount']
        transaction_table.insert_one(tx)
        return tx

    if cmd == "BUY" or cmd == "SELL":
        tx["type"] = "accountTransaction"
        tx['server'] = "TS1"
        tx["amount"] = data['amount']
        tx["sym"] = data['sym']
        tx["flag"] = "pending"
        transaction_table.insert_one(tx)
        return tx

    if cmd in ["COMMIT_SELL", "CANCEL_SELL", "COMMIT_BUY", "CANCEL_BUY", "CANCEL_SET_SELL", "CANCEL_SET_BUY"]:
        tx["type"] = "accountTransaction"
        tx['server'] = "TS1"
        transaction_table.insert_one(tx)
        return tx

    if cmd in ["SET_SELL_AMOUNT", "SET_SELL_TRIGGER", "SET_BUY_AMOUNT", "SET_BUY_TRIGGER"]:
        tx["type"] = "accountTransaction"
        tx['server'] = "TS1"
        tx["sym"] = data['sym']
        tx["amount"] = data['amount']
        transaction_table.insert_one(tx)
        return tx

    return tx


'''
Helper function to check if a user exists or not.
Parameters: username (str)
'''


def account_exists(username):
    query = {"username": username}
    if user_table.find_one(query):
        return True
    return False


# returns the most recent pending transaction as a dictionary {}
def recent_transaction(username, cmd, timestamp):
    greater_than_time = timestamp - 60
    # create the pipeline
    pipeline = [
        # add $match stage to filter by username
        {"$match": {"username": username}},
        {
            "$project": {
                "_id": 0,
                "transaction": {
                    "$filter": {
                        "input": "$transactions",
                        "as": "transaction",
                        "cond": {
                            "$and": [
                                {"$eq": ["$$transaction.command", cmd]},
                                {"$eq": ["$$transaction.flag", "pending"]},
                                {"$gte": ["$$transaction.timestamp",
                                          greater_than_time]}
                            ]
                        }
                    }
                }
            }
        }
    ]
    # perform the aggregation pipeline to match and extract the desired fields
    tx = list(user_table.aggregate(pipeline + [{"$unwind": "$transaction"}]))
    if len(tx) > 0:
        return tx[len(tx) - 1]['transaction']
    return {}


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
