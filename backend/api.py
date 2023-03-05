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
            "flag":"",
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


# TODO add error checking if insufficient funds
@app.route("/buy", methods=["POST"])
def buy():
    data = request.json
    if not account_exists(data['username']):
        new_transaction(data, error="The specified user does not exist.")
    filter = {"username":data['username']}
    tx = new_transaction(data)
    new_tx = {"$push": { "transactions": tx}}
    # update the array of transactions to include a buy
    user_table.update_one(filter, new_tx)
    return "Added to transactions. 60 seconds to COMMIT"


# TODO add error checking
@app.route("/commit_buy", methods=["POST"])
def commit_buy():
    data = request.json
    timestamp = time.time()
    greater_than_time = timestamp - 60

    # filter to get only commands of type BUY in the correct time
    filter = {
        "username": data["username"],
        "transactions": {
            "$elemMatch": {
            "command": "BUY",
            "timestamp": {
                "$gte": greater_than_time
                }
            }
        }
    }

    # create the projection to extract only the price field from the matching transaction
    fields = {
        "_id": 0,
        "price": {
            "$filter": {
            "input": "$transactions",
            "as": "transaction",
            "cond": {
                "$and": [
                { "$eq": [ "$$transaction.command", "BUY" ] },
                { "$gte": [ "$$transaction.timestamp", greater_than_time ] }
                ]
            }
            }
        }
    }

    # perform the aggregation pipeline to match and extract the desired fields
    valid_buy = list(user_table.aggregate([
            { "$match": filter },
            { "$project": fields }
        ]
    ))

    if len(valid_buy) > 0:
        # subtract the funds and add the stock to user's stocks and add new transaction
        valid_buy = list(valid_buy)[0]
        buy_price = valid_buy["price"][0]["price"]
        stock_bought = valid_buy["price"][0]["sym"]
        print("STOCK BOUGHT", stock_bought)
        balance = user_table.find_one({"username":data["username"]})["funds"]
        update_funds = {"$set": {"funds": float(balance) - buy_price},             
                        "$push": {"transactions": {
                            "timestamp":timestamp,
                            "server":"TS1",
                            "transactionNum":data['trxNum'],
                            "command":data['cmd']
                        }, 
                        "stocks": {"sym":stock_bought}},
                        }
        user_table.update_one({"username":data["username"]}, update_funds)

        return "Successfly bought stock"

    # add just a new transaction
    new_tx = {"$push": { "transactions": {
            "timestamp":timestamp,
            "server":"TS1",
            "transactionNum":data['trxNum'],
            "command":data['cmd'],
            }
        }
    }

    user_table.update_one({"username":data["username"]}, new_tx)
    
    return "No valid buys"


# TODO
@app.route("/cancel_buy", methods=["POST"])
def cancel_buy():
    # check if a BUY command was executed in the last 60 seconds

    # if yes, cancel the transaction (remove pending flag)
    # dont add to stocks[]
    pass


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
        new_transaction(data, error="The specified user does not exist.")

    filter = {"username":data['username']}
    user_stocks = user_table.find_one(filter)['stocks']
    # check if owned stock is >= amount being sold
    valid_transaction = False
    for x in user_stocks:
        if (x['stockSymbol'] == data['sym']) and (float(x['amount']) > float(data['amount'])):
            valid_transaction = True
    if valid_transaction:
        #add to transactions[]
        tx = new_transaction(data)
        update = {"$push": {"transactions": tx}}
        user_table.update_one(filter, update)   
    return 'Added to transactions. 60 seconds to COMMIT'


# TODO error checking and adding the flag functionality
@app.route("/commit_sell", methods=["POST"])
def commit_sell():
    # check if a SELL command was executed in the last 60 seconds
    data = request.json
    if not account_exists(data['username']):
        new_transaction(data, error="The specified user does not exist.")
    timestamp = time.time()
    recent_tx = recent_transactions(data['username'], "SELL", timestamp)

    if len(recent_tx) > 0:
        # get the most recent index
        i = len(recent_tx) - 1
        stock = recent_tx[i]['transaction'][0]['stockSymbol']
        sell_price = recent_tx[i]["transaction"][0]["amount"]
        user_filter = {"username": data['username']}
        stock_filter = {"username": data['username'], "stocks.sym": stock}
        balance = user_table.find_one(user_filter)['funds']
        amount_owned = user_table.find_one(stock_filter, {"stocks.$": 1})['stocks'][0]['amount']
        update_funds = {"$set": {"funds": float(sell_price) + float(balance)}}
        user_table.update_one(user_filter, update_funds)
        new_price = float(amount_owned) - float(sell_price)
        update_stock = {"$set": {"stocks.$.amount": new_price}}
        user_table.update_one(stock_filter, update_stock)
        update_transaction = {"$push": { "transactions": {
            "timestamp":timestamp,
            "server":"TS1",
            "transactionNum":data['trxNum'],
            "command":data['cmd'],
            }}
        }
        user_table.update_one(user_filter, update_transaction)
        for d in user_table.find():
            print(d)
        return "Successfly sold stock!"
    else:
        
        update_transaction = {"$push": { "transactions": {
            "timestamp":timestamp,
            "server":"TS1",
            "transactionNum":data['trxNum'],
            "command":data['cmd'],
            }}
        }
        user_table.update_one(user_filter, update_transaction)
        return "No valid Sells"


@app.route("/cancel_sell", methods=["POST"])
def cancel_sell():
    # For Testing:
    # user_table.insert_one({
    #     "username":"test",
    #     "funds":"5000.0",
    #     "stocks":[{"sym":"AP", "amount":"10000.0"}, {"sym":"GO", "amount":"2000"}],
    #     "transactions":[
    #         {"timestamp":time.time(), "command":"SELL", "stockSymbol":"AP", "amount":"500", "flag":"pending", "transactionNum":"1"},
    #         {"timestamp":time.time(), "command":"BUY", "stockSymbol":"AP", "amount":"500"},
    #         {"timestamp":time.time(), "command":"ADD", "amount":"1000"}
    #     ]
    # })
    # check if a SELL command was executed in the last 60 seconds
    data = request.json
    timestamp = time.time()
    user_filter = {"username": data['username']}
    recent_tx = recent_transactions(data['username'], "SELL", timestamp)
    print("recent_tx", recent_tx)

    if len(recent_tx) > 0 :
        # get the most recent transaction
        i = len(recent_tx) - 1
        print('index', i)
        flag = recent_tx[0]['transaction'][0]['flag']
        if flag == "pending":
            # Update the "flag" field for the most recent SELL transaction
            txNum = recent_tx[0]['transaction'][0]['transactionNum']
            user_table.update_one(
                {"username": data['username'], "transactions.transactionNum": txNum},
                {"$set": {"transactions.$.flag": "cancelled"}}
            )
            # Add the new CANCEL_SELL transaction to the list
            newTx = new_transaction(data)
            user_table.update_one(user_filter, {"$push": { "transactions": newTx}})
            return "Transaction has been cancelled"
        new_transaction(data, error="No recent SELL transactions.")
        return "No recent sell transactions"
    else:
        for x in user_table.find():
            print(x)
        new_transaction(data, error="No recent SELL transactions.")
        return "No recent sell transactions"


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
    if "error" in atr:
        tx = {
            "type":"errorEvent",
            "timestamp":time.time(),
            "server":"TS1",
            "transactionNum":data['trxNum'],
            "command":cmd,
            "username": data['username'],
            "errorMessage":atr['error']
        }
        transaction_table.insert_one(tx)
        return tx
    
    if cmd == 'ADD':
        tx = {
            "type":"accountTransaction",
            "timestamp":time.time(),
            "server":"TS1",
            "transactionNum":data['trxNum'],
            "command":cmd,
            "username": data['username'],
            "amount":data['amount']
        }

    if cmd == "BUY" or cmd == "SELL":
        tx["sym"] = data['sym']
        tx["flag"] = "pending"
    
    if cmd in ["COMMIT_BUY", "COMMIT_SELL", "CANCEL_BUY", "CANCEL_SELL"]:
        tx = {
            "type":"accountTransaction",
            "timestamp":time.time(),
            "server":"TS1",
            "transactionNum":data['trxNum'],
            "command":cmd,
            "username": data['username']
        }
    
    transaction_table.insert_one(tx)
    return tx


# returns a list of transactions within 60 seconds
def recent_transactions(username, cmd, timestamp):
    greater_than_time = timestamp - 60

    # filter to get only commands of type SELL in the correct time
    filter = {
        "username": username,
        "transactions": {
            "$elemMatch": {
            "command": cmd,
            "timestamp": {
                "$gte": greater_than_time
                }
            }
        }
    }

    # create the projection
    fields = {
        "_id": 0,
        "transaction": {
            "$filter": {
            "input": "$transactions",
            "as":"transaction",
            "cond": {
                "$and": [
                { "$eq": [ "$$transaction.command", cmd ] },
                { "$gte": [ "$$transaction.timestamp", greater_than_time ] }
                ]
            }
            }
        }
    }
    #sell_transactions = user_table.find_one(filter)
    # perform the aggregation pipeline to match and extract the desired fields
    return list(user_table.aggregate([
            { "$match": filter },
            { "$project": fields }
        ]
    ))



if __name__ =="__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)