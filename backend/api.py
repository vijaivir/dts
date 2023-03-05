from flask import Flask, request
from pymongo import MongoClient
import xml.etree.ElementTree as ET
import time
import requests

client = MongoClient()
db = client.user_database
# Create two collections (user_table, transaction_table)
user_table = db.user_table
transaction_table = db.transaction_table

app = Flask(__name__)

"""
Database Structure:
{
    "username":"",
    "funds":"",
    "reserve":"",
    "stocks":[
        {
            "sym":"",
            "amount":""
        }
    ],
    "transactions":[
        {
            "type":"",
            "timestamp":"",
            "server":"", (TS1 or QS1)
            "transactionNum":"",
            "command":"",
            "flag":"", (pending, complete, or cancelled)
            "username":"",
            "sym":"", (does not apply to ADD)
            "amount":"", (could mean "funds" or "price". name it "amount" for simplicity)
            "cryptokey":"", (only for QUOTE)
            "errorMessage":"" (only for erroneous transactions)
        }
    ]
}
"""

@app.route("/quote", methods=["POST"])
def get_quote():
    quote_price = requests.get('http://fe26-2604-3d08-2679-2000-c58a-51ec-8599-b312.ngrok.io/quote')
    res = quote_price.json()
    price = res['price']
    return price


@app.route("/add", methods=["POST"])
def add():
    # recive data from API
    data = request.json
    filter = {"username":data['username']}
    tx = new_transaction(data)
    # if user not in user_table, create new user
    if not account_exists(data['username']):
        user_table.insert_one({
            "username":data['username'],
            "funds":data['amount'],
            "stocks":[],
            "transactions":[tx]
        })
        return "created account"
    # else, update existing user
    else:
        balance = user_table.find_one(filter)["funds"]
        update = {"$set": {"funds": float(balance) + float(data['amount'])},
                  "$push": {"transactions": tx}}
        user_table.update_one(filter, update)
    return "updated account"


@app.route("/display_summary", methods=["POST"])
def display_summary():
    pass


@app.route("/buy", methods=["POST"])
def buy():
    data = request.json
    # check if account exists
    if not account_exists(data['username']):
        return str(new_transaction(data, error="The specified user does not exist."))

    filter = {"username":data['username']}
    funds = user_table.find_one(filter)['funds']

    # check if sufficient funds to buy
    if funds >= data['amount']:
        #add to transactions[]
        tx = new_transaction(data)
        update = {"$push": {"transactions": tx}}
        user_table.update_one(filter, update)   
        return 'Added to transactions. 60 seconds to COMMIT'
    # else create an error transaction for the transaction_table
    return str(new_transaction(data, error="Insufficient funds."))



@app.route("/commit_buy", methods=["POST"])
def commit_buy():
    data = request.json

    # check if account exists
    if not account_exists(data['username']):
        return str(new_transaction(data, error="The specified user does not exist."))
    
    # get the most recent BUY transaction with the pending flag
    timestamp = time.time()
    recent_tx = recent_transaction(data['username'], "BUY", timestamp)

    if len(recent_tx) == 0:
        # no recent BUY transactions found, create an error transaction for the transaction_table
        return str(new_transaction(data, error="No recent BUY transactions."))
    else:
        filter = {"username":data['username']}
        stock = recent_tx['sym']
        price = recent_tx['amount']
        txNum = recent_tx['transactionNum']

        # subtract from user funds
        balance = user_table.find_one(filter)['funds']
        user_table.update_one(filter, {"$set": {"funds": float(balance) - float(price)}})

        # check if user owns the stock already
        stock_filter = {"username": data['username'], "stocks.sym": stock}
        stock_owned = user_table.find_one(stock_filter, {"stocks.$": 1})
        if stock_owned:
            # update stock
            amount_owned = stock_owned['stocks'][0]['amount']
            user_table.update_one(stock_filter, {"$set": {"stocks.$.amount": float(amount_owned) + float(price)}} )
        else:
            # create a new stock
            user_table.update_one(filter, {"$push": { "stocks": {'sym':stock, 'amount':price}}})
        
        # set pending flag to complete
        user_table.update_one(
                {"username": data['username'], "transactions.transactionNum": txNum},
                {"$set": {"transactions.$.flag": "complete"}}
            )
        
        # add the COMMIT_BUY transaction to the user table (new_transaction() auto adds to transaction_table)
        user_table.update_one(filter, {"$push": { "transactions": new_transaction(data)}})

        return 'Successfully committed.'


# TODO
@app.route("/cancel_buy", methods=["POST"])
def cancel_buy():
    data = request.json

    # check if account exists
    if not account_exists(data['username']):
        return str(new_transaction(data, error="The specified user does not exist."))
    
    # get the most recent transaction with the pending flag
    timestamp = time.time()
    recent_tx = recent_transaction(data['username'], "BUY", timestamp)
    
    if len(recent_tx) == 0:
        # no recent BUY transactions found, create an error transaction for the transaction_table
        return str(new_transaction(data, error="No recent BUY transactions."))
    else:
        filter = {"username":data['username']}
        txNum = recent_tx['transactionNum']

        # set pending flag to cancelled
        user_table.update_one(
                {"username": data['username'], "transactions.transactionNum": txNum},
                {"$set": {"transactions.$.flag": "cancelled"}}
            )

        # add the CANCEL_SELL transaction to the user table (new_transaction() auto adds to transaction_table)
        user_table.update_one(filter, {"$push": { "transactions": new_transaction(data)}})

        return 'Successfully cancelled.'


# TODO
@app.route("/set_buy_amount", methods=["POST"])
def set_buy_amount():
    pass


# TODO
@app.route("/set_buy_trigger", methods=["POST"])
def set_buy_trigger():
    pass


# TODO
@app.route("/cancel_set_buy", methods=["POST"])
def cancel_set_buy():
    pass


@app.route("/sell", methods=["POST"])
def sell():
    data = request.json
    # check if account exists
    if not account_exists(data['username']):
        return str(new_transaction(data, error="The specified user does not exist."))

    filter = {"username":data['username']}
    user_stocks = user_table.find_one(filter)['stocks']
    # check if owned stock is >= amount being sold
    valid_transaction = False
    for x in user_stocks:
        if (x['sym'] == data['sym']) and (float(x['amount']) > float(data['amount'])):
            valid_transaction = True
    if valid_transaction:
        # add the SELL transaction to the user table (new_transaction() auto adds to transaction_table)
        user_table.update_one(filter, {"$push": {"transactions": new_transaction(data)}})   
        return 'Added to transactions. 60 seconds to COMMIT'
    # else create an error transaction for the transaction_table
    return str(new_transaction(data, error="Insufficient stock amount."))


# TODO error checking and adding the flag functionality
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
        filter = {"username":data['username']}
        stock = recent_tx['sym']
        price = recent_tx['amount']
        txNum = recent_tx['transactionNum']

        # subtract stock amount
        stock_filter = {"username": data['username'], "stocks.sym": stock}
        amount_owned = user_table.find_one(stock_filter, {"stocks.$": 1})['stocks'][0]['amount']
        user_table.update_one(stock_filter, {"$set": {"stocks.$.amount": float(amount_owned) - float(price)}} )

        # add to user funds
        balance = user_table.find_one(filter)['funds']
        user_table.update_one(filter, {"$set": {"funds": float(price) + float(balance)}})

        # set pending flag to complete
        user_table.update_one(
                {"username": data['username'], "transactions.transactionNum": txNum},
                {"$set": {"transactions.$.flag": "complete"}}
            )
        
        # add the COMMIT_SELL transaction to the user table (new_transaction() auto adds to transaction_table)
        user_table.update_one(filter, {"$push": { "transactions": new_transaction(data)}})

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
        filter = {"username":data['username']}
        txNum = recent_tx['transactionNum']

        # set pending flag to cancelled
        user_table.update_one(
                {"username": data['username'], "transactions.transactionNum": txNum},
                {"$set": {"transactions.$.flag": "cancelled"}}
            )

        # add the CANCEL_SELL transaction to the user table (new_transaction() auto adds to transaction_table)
        user_table.update_one(filter, {"$push": { "transactions": new_transaction(data)}})

        return 'Successfully cancelled.'



# TODO
@app.route("/set_sell_amount", methods=["POST"])
def set_sell_amount():
    data = request.json
    if not account_exists(data['username']):
        new_transaction(data, error="The specified user does not exist.")
    



# TODO
@app.route("/set_sell_trigger", methods=["POST"])
def set_sell_trigger():
    pass


# TODO
@app.route("/cancel_set_sell", methods=["POST"])
def cancel_set_sell():
    pass

@app.route("/dumplog", methods=["POST"])
def dumplog():
    # user_table.insert_one({
    #     "username":"test",
    #     "funds":"5000.0",
    #     "stocks":[{"sym":"AP", "amount":"10000.0"}, {"sym":"GO", "amount":"2000"}],
    #     "transactions":[
    #         {"type":"userCommand", "timestamp":time.time(), "command":"SELL", "stockSymbol":"AP", "amount":"500"},
    #         {"type":"systemEvent", "timestamp":time.time(), "command":"BUY", "stockSymbol":"AP", "amount":"500"}
    #     ]
    # })
    data = request.json
    filter = {"username":data['username']}
    user_transactions = user_table.find_one(filter)['transactions']
    root = ET.Element("log")
    for t in user_transactions:
        transaction = ET.SubElement(root, "userCommand")
        
        #TODO: add error checking to ensure that the transaction contains the attribute
        # Add the transaction attributes
        ET.SubElement(transaction, "timestamp").text = str((t["timestamp"]))
        ET.SubElement(transaction, "command").text = t["command"]
        ET.SubElement(transaction, "username").text = data["username"]
        ET.SubElement(transaction, "amount").text = t["amount"]

    return ET.tostring(root)


@app.route("/clear", methods=["GET"])
def clear():
    user_table.delete_many({})

    return "cleared DB"


'''
Helper function to check if a user exists or not.
Parameters: username (str)
'''
def account_exists(username):
    query = {"username":username}
    if user_table.find_one(query):
        return True
    return False


def new_transaction(data, **atr):
    cmd = data['cmd']
    
    # default attributes
    tx = {
        "timestamp":time.time(),
        "transactionNum":data['trxNum'],
        "command":cmd,
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
        tx["amount"] = data['amount']
        tx["sym"] = data['sym']
        tx["flag"] = "pending"
        transaction_table.insert_one(tx)
        return tx
    
    if cmd == "COMMIT_SELL" or cmd == "CANCEL_SELL" or cmd == "COMMIT_BUY" or cmd == "CANCEL_BUY":
        tx["type"] = "accountTransaction"
        tx['server'] = "TS1"
        transaction_table.insert_one(tx)
        return tx

    return tx


# returns the most recent pending transaction as a dictionary {}
def recent_transaction(username, cmd, timestamp):
    greater_than_time = timestamp - 60
    # create the pipeline
    pipeline = [
        {"$match": {"username": username}}, # add $match stage to filter by username
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
                                {"$gte": ["$$transaction.timestamp", greater_than_time]}
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



if __name__ =="__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)