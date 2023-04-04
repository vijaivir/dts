from flask import Flask, request, jsonify
from pymongo import MongoClient
import xml.etree.ElementTree as ET
import xml.dom.minidom
import time
import requests
import redis
import json

print("STARTING")

# container name for redis cache
redis_client = redis.Redis(host="redis_client", port=6379,db=0)

# container name for mongo db
client = MongoClient("mongodb://mongo_database", 27017)
#client = MongoClient()

db = client.user_database
# Create two collections (user_table, transaction_table)
user_table = db.user_table
transaction_table = db.transaction_table

app = Flask(__name__) 

@app.route("/quote", methods=["POST"])
def get_quote():
    data = request.json
    quote_price = quote(data['sym'], data['username'])

    return quote_price


def quote(sym, username):
    filter = {"username":username}
    # quote_price = requests.get('http://fe26-2604-3d08-2679-2000-c58a-51ec-8599-b312.ngrok.io/quote')
    cached_quote = redis_client.get(sym)
    if cached_quote is not None:
        print("FROM CACHE")
        cached_quote = json.loads(cached_quote)
        cached_quote['username'] = username
        cached_quote['sym'] = sym
        res = cached_quote
    else:
        quote_price = requests.get('http://quoteserver:5001/quoteserver/quote')
        res = quote_price.json()       
        res['quoteServerTime'] = time.time()
        res['cmd'] = "QUOTE"
        redis_client.set(sym, json.dumps(res))
        redis_client.expire(sym, 120)

        res['username'] = username
        res['sym'] = sym
    tx = new_transaction(res)
    user_table.update_one(filter, {"$push": {"transactions": tx}})
    update_stocks(sym, res['price'], username)
    return res


# Called after quote(): updates stock amount based on current price
# also executes any triggers
def update_stocks(sym, price, username):
    # if the user owns stock (sym) update the amount based on their shares
    filter = {'username': username}
    stock_filter = {"username": username, "stocks.sym": sym}
    stock_owned = user_table.find_one(stock_filter, {"stocks.$": 1})

    # update stocks[]
    if stock_owned:
        share = stock_owned['stocks'][0]['share']
        new_amount = float(price) * float(share)
        user_table.update_one(stock_filter, {"$set": {"stocks.$.amount": new_amount}})

    # check reserved_buy for any triggers and execute
    buy_filter = {"username": username, "reserved_buy.sym": sym, "reserved_buy.trigger": {"$exists": True}}
    set_buy = user_table.find_one(buy_filter, {"reserved_buy.$": 1})

    if set_buy:
        # check if price is less than or equal to trigger price
        buy_trigger = set_buy['reserved_buy'][0]['trigger']
        buy_amount = set_buy['reserved_buy'][0]['amount']
        new_share = float(buy_amount) // float(price)
        if float(price) <= float(buy_trigger):
            # buy the stock

            # check if user owns the stock already
            stock_owned = user_table.find_one(stock_filter, {"stocks.$": 1})
            if stock_owned:
                # update stock
                amount_owned = stock_owned['stocks'][0]['amount']
                share_owned = stock_owned['stocks'][0]['share']
                user_table.update_one(stock_filter, {"$set": {"stocks.$.amount": float(buy_amount) + float(amount_owned)}})
                user_table.update_one(stock_filter, {"$set": {"stocks.$.share": float(share_owned) + float(new_share)}} )
            else:
                # create a new stock
                user_table.update_one(filter, {"$push": { "stocks": {'sym':sym, 'amount':buy_amount, 'share':new_share}}})
            
            # remove from reserved_buy
            user_table.update_one({"username": username, "reserved_buy.sym": sym}, {"$pull": {"reserved_buy": {"sym": sym}}})

            # create a new transaction
            tx = {
                "timestamp":time.time(),
                "command":"AUTO_BUY",
                "username": username,
                "type": "automaticTransaction",
                'server':"TS1",
                "amount": buy_amount,
                "sym":sym
            }
            transaction_table.insert_one(tx)
            update = {"$push": {"transactions": tx}}
            user_table.update_one({"username":username}, update)


    # check reserved_sell for any triggers and execute
    sell_filter = {"username": username, "reserved_sell.sym": sym, "reserved_sell.trigger": {"$exists": True}}
    set_sell = user_table.find_one(sell_filter, {"reserved_sell.$": 1})

    if set_sell:
        # check if price is less than or equal to trigger price
        sell_trigger = set_sell['reserved_sell'][0]['trigger']
        if float(price) >= float(sell_trigger):
            # sell the stock
            amount_sold = set_sell['reserved_sell'][0]['amount']
            user_funds = user_table.find_one({'username':username})['funds']
            user_table.update_one({'username':username}, {"$set": {"funds": float(amount_sold) + float(user_funds)}})

            # remove from reserved_sell
            user_table.update_one({"username": username, "reserved_sell.sym": sym}, {"$pull": {"reserved_sell": {"sym": sym}}})

            # create a new transaction
            tx = {
                "timestamp":time.time(),
                "command":"AUTO_SELL",
                "username": username,
                "type": "automaticTransaction",
                'server':"TS1",
                "amount": amount_sold,
                "sym":sym
            }
            transaction_table.insert_one(tx)
            update = {"$push": {"transactions": tx}}
            user_table.update_one({"username":username}, update)
            
    return "Updated Stocks"

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
            "reserved_buy": [],
            "reserverd_sell": [],
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


@app.route("/buy", methods=["POST"])
def buy():
    data = request.json
    filter = {"username":data['username']}
    # check if account exists
    if not account_exists(data['username']):
        return str(new_transaction(data, error="The specified user does not exist!"))

    # check if sufficient funds to buy
    funds = user_table.find_one(filter)['funds']
    if float(funds) < float(data['amount']):
        # create an error transaction for the transaction_table
        return str(new_transaction(data, error="Insufficient funds."))
    
    # get the current stock price
    stock_quote = quote(data['sym'], data['username'])
    stock_price = stock_quote['price']

    # share that can be bought with the specified price rounded to the nearest whole number
    share = float(data['amount']) // float(stock_price)
    data['share'] = share

    #add to transactions[]
    tx = new_transaction(data)
    update = {"$push": {"transactions": tx}}
    user_table.update_one(filter, update)   
    return 'Added to transactions. 60 seconds to COMMIT'


@app.route("/commit_buy", methods=["POST"])
def commit_buy():
    data = request.json

    # check if account exists
    if not account_exists(data['username']):
        return str(new_transaction(data, error="The specified user does not exist!"))
    
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
        share = recent_tx['share']

        # subtract from user funds
        funds = user_table.find_one(filter)['funds']
        user_table.update_one(filter, {"$set": {"funds": float(funds) - float(price)}})

        # check if user owns the stock already
        stock_filter = {"username": data['username'], "stocks.sym": stock}
        stock_owned = user_table.find_one(stock_filter, {"stocks.$": 1})
        if stock_owned:
            # update stock
            amount_owned = stock_owned['stocks'][0]['amount']
            share_owned = stock_owned['stocks'][0]['share']
            user_table.update_one(stock_filter, {"$set": {"stocks.$.amount": float(amount_owned) + float(price)}} )
            user_table.update_one(stock_filter, {"$set": {"stocks.$.share": float(share_owned) + float(share)}} )
        else:
            # create a new stock
            user_table.update_one(filter, {"$push": { "stocks": {'sym':stock, 'amount':price, 'share':share}}})
        
        # set pending flag to complete
        user_table.update_one(
                {"username": data['username'], "transactions.transactionNum": txNum},
                {"$set": {"transactions.$.flag": "complete"}}
            )
        
        # add the COMMIT_BUY transaction to the user table (new_transaction() auto adds to transaction_table)
        user_table.update_one(filter, {"$push": { "transactions": new_transaction(data)}})

        return 'Successfully committed.'
    

@app.route("/cancel_buy", methods=["POST"])
def cancel_buy():
    data = request.json

    # check if account exists
    if not account_exists(data['username']):
        return str(new_transaction(data, error="The specified user does not exist!"))
    
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

        # add the CANCEL_BUY transaction to the user table (new_transaction() auto adds to transaction_table)
        user_table.update_one(filter, {"$push": { "transactions": new_transaction(data)}})

        return 'Successfully cancelled.'


@app.route("/set_buy_amount", methods=["POST"])
def set_buy_amount():
    data = request.json
    if not account_exists(data['username']):
        new_transaction(data, error="The specified user does not exist!")
    filter = {"username":data['username']}
    
    reserve_amount = data['amount']
    # check if the user has the necessary funds
    balance = user_table.find_one(filter)["funds"]
    if float(balance) < float(reserve_amount):
        new_transaction(data, error="Insufficient Funds.")
        return "Insufficient Funds"

    update = {"$set": {"funds": float(balance) - float(reserve_amount)},             
                "$push": {
                    "reserved_buy": {
                        "amount":reserve_amount, "sym": data['sym']
                        }
                    },
                }

    user_table.update_one(filter, update)
    tx = new_transaction(data)
    new_tx = {"$push": { "transactions": tx}}
    user_table.update_one(filter, new_tx)
    return "Set Buy Amount"



@app.route("/set_buy_trigger", methods=["POST"])
def set_buy_trigger():
    data = request.json
    filter = {"username":data['username']}
    if not account_exists(data['username']):
        new_transaction(data, error="The specified user does not exist!")

    # see if the user has a previous set buy for the stock requested
    valid_set_buy = user_table.find_one({
        "username": data['username'],
        "reserved_buy": {
            "$elemMatch": {
                "sym": data['sym']
            }
        }   
    })

    if not valid_set_buy:
        new_transaction(data, error="No prereq SET_BUY_AMOUNT")
        return f"No prereq SET_BUY_AMOUNT for stock {data['sym']}"
    
    trigger = data['amount']
    reserved_filter = {"username": data['username'], "reserved_buy.sym": data['sym']}
    user_table.update_one(reserved_filter, {"$set": {"reserved_buy.$.trigger": trigger}})

    tx = new_transaction(data)
    new_tx = {"$push": { "transactions": tx}}
    user_table.update_one(filter, new_tx)
    return "Set Buy Trigger"



@app.route("/cancel_set_buy", methods=["POST"])
def cancel_set_buy():
    data = request.json
    filter = {"username":data['username']}
    if not account_exists(data['username']):
        new_transaction(data, error="The specified user does not exist!")
    valid_reserve = user_table.find_one({"username": data['username'], "reserved_buy.sym": data['sym']}, 
                                        {"_id": 0, "reserved_buy.$": 1})

    if not valid_reserve:
        new_transaction(data, error="No prereq SET_BUY_AMOUNT")
        return f"No prereq SET_BUY_AMOUNT for stock {data['sym']}"

    balance = user_table.find_one(filter)["funds"]
    reserve_amount = valid_reserve['reserved_buy'][0]["amount"]
    update = {"$set": {"funds": float(balance) + float(reserve_amount)},             
                "$pull": {
                    "reserved_buy": {
                        "amount":reserve_amount, "sym": data['sym']
                        }
                    },
                }
    user_table.update_one(filter, update)
    tx = new_transaction(data)
    new_tx = {"$push": { "transactions": tx}}
    user_table.update_one(filter, new_tx)

    return "Cancelled SET_BUY"


@app.route("/dumplog", methods=["POST"])
def dumplog():
    data = request.json

    #username was provided
    if 'username' in data:
        if not account_exists(data['username']):
            return "The specified user does not exist!"

        filter = {"username":data['username']}
        user_transactions = user_table.find_one(filter)['transactions']
        root = ET.Element("log")
        for t in user_transactions:
            if t['type'] == 'accountTransaction':
                transaction = ET.SubElement(root, "accountTransaction")
                ET.SubElement(transaction, "timestamp").text = str((t["timestamp"]))
                ET.SubElement(transaction, "transactionNum").text = str((t["transactionNum"]))
                ET.SubElement(transaction, "command").text = t["command"]
                ET.SubElement(transaction, "username").text = t["username"]
                ET.SubElement(transaction, "server").text = t["server"]

                if t['command'] == 'ADD':
                    ET.SubElement(transaction, "amount").text = str(t["amount"])
                if t['command'] in ["BUY", "SELL", "SET_SELL_AMOUNT", "SET_SELL_TRIGGER", "SET_BUY_AMOUNT", "SET_BUY_TRIGGER"]:
                    ET.SubElement(transaction, "amount").text = str(t["amount"])
                    ET.SubElement(transaction, "stockSymbol").text = t["sym"]

            elif t['type'] == 'errorEvent':
                transaction = ET.SubElement(root, "errorEvent")
                ET.SubElement(transaction, "timestamp").text = str((t["timestamp"]))
                ET.SubElement(transaction, "transactionNum").text = str((t["transactionNum"]))
                ET.SubElement(transaction, "command").text = t["command"]
                ET.SubElement(transaction, "username").text = t["username"]
                ET.SubElement(transaction, "server").text = t["server"]
                ET.SubElement(transaction, "errorMessage").text = str(t["error"])

            elif t['type'] == 'quoteServer':
                transaction = ET.SubElement(root, "quoteServer")
                ET.SubElement(transaction, "timestamp").text = str((t["timestamp"]))
                ET.SubElement(transaction, "username").text = t["username"]
                ET.SubElement(transaction, "server").text = t["server"]
                ET.SubElement(transaction, "stockSymbol").text = t["sym"]
                ET.SubElement(transaction, "stockPrice").text = str(t["stockPrice"])
                ET.SubElement(transaction, "quoteServerTime").text = str((t["quoteServerTime"]))
                ET.SubElement(transaction, "cryptokey").text = t["cryptokey"]

            elif t['type'] == 'automaticTransaction':
                transaction = ET.SubElement(root, "automaticTransaction")
                ET.SubElement(transaction, "timestamp").text = str((t["timestamp"]))
                ET.SubElement(transaction, "username").text = t["username"]
                ET.SubElement(transaction, "server").text = t["server"]
                ET.SubElement(transaction, "stockSymbol").text = t["sym"]
                ET.SubElement(transaction, "amount").text = str(t["amount"])
                ET.SubElement(transaction, "command").text = t["command"]


        xml_str = ET.tostring(root)
        pretty_xml = xml.dom.minidom.parseString(xml_str).toprettyxml()
        with open(data['filename'], 'wb') as f:
            f.write(pretty_xml.encode('utf-8'))
    
    # no username - print from the transaction_table
    else:
        root = ET.Element("log")
        for t in transaction_table.find():
            if t['type'] == 'accountTransaction':
                transaction = ET.SubElement(root, "accountTransaction")
                ET.SubElement(transaction, "timestamp").text = str((t["timestamp"]))
                ET.SubElement(transaction, "transactionNum").text = str((t["transactionNum"]))
                ET.SubElement(transaction, "command").text = t["command"]
                ET.SubElement(transaction, "username").text = t["username"]
                ET.SubElement(transaction, "server").text = t["server"]

                if t['command'] == 'ADD':
                    ET.SubElement(transaction, "amount").text = str(t["amount"])
                if t['command'] in ["BUY", "SELL", "SET_SELL_AMOUNT", "SET_SELL_TRIGGER", "SET_BUY_AMOUNT", "SET_BUY_TRIGGER"]:
                    ET.SubElement(transaction, "amount").text = str(t["amount"])
                    ET.SubElement(transaction, "stockSymbol").text = t["sym"]

            elif t['type'] == 'errorEvent':
                transaction = ET.SubElement(root, "errorEvent")
                ET.SubElement(transaction, "timestamp").text = str((t["timestamp"]))
                ET.SubElement(transaction, "transactionNum").text = str((t["transactionNum"]))
                ET.SubElement(transaction, "command").text = t["command"]
                ET.SubElement(transaction, "username").text = t["username"]
                ET.SubElement(transaction, "server").text = t["server"]
                ET.SubElement(transaction, "errorMessage").text = str(t["error"])

            elif t['type'] == 'quoteServer':
                transaction = ET.SubElement(root, "quoteServer")
                ET.SubElement(transaction, "timestamp").text = str((t["timestamp"]))
                ET.SubElement(transaction, "username").text = t["username"]
                ET.SubElement(transaction, "server").text = t["server"]
                ET.SubElement(transaction, "stockSymbol").text = t["sym"]
                ET.SubElement(transaction, "stockPrice").text = str(t["stockPrice"])
                ET.SubElement(transaction, "quoteServerTime").text = str((t["quoteServerTime"]))
                ET.SubElement(transaction, "cryptokey").text = t["cryptokey"]

            elif t['type'] == 'automaticTransaction':
                transaction = ET.SubElement(root, "automaticTransaction")
                ET.SubElement(transaction, "timestamp").text = str((t["timestamp"]))
                ET.SubElement(transaction, "username").text = t["username"]
                ET.SubElement(transaction, "server").text = t["server"]
                ET.SubElement(transaction, "stockSymbol").text = t["sym"]
                ET.SubElement(transaction, "amount").text = str(t["amount"])
                ET.SubElement(transaction, "command").text = t["command"]


        xml_str = ET.tostring(root)
        pretty_xml = xml.dom.minidom.parseString(xml_str).toprettyxml()
        with open(data['filename'], 'wb') as f:
            f.write(pretty_xml.encode('utf-8'))

    return pretty_xml.encode('utf-8')


@app.route("/testing", methods=["GET"])
def testing():
    return "ITS WORKING FROM BUY"


@app.route("/clear", methods=["GET"])
def clear():
    user_table.delete_many({})
    transaction_table.delete_many({})
    return "cleared DB"


'''
Helper function to check if a user exists or not.
Parameters: username (str)
'''
def account_exists(username):
    query = {"username":username}
    if user_table.find_one({"username": username}):
        return True
    return False


def new_transaction(data, **atr):
    cmd = data['cmd']
    
    # default attributes
    tx = {
        "timestamp":time.time(),
        "command":cmd,
        "username": data['username'],
    }

    if "error" in atr:
        tx["transactionNum"] = data['trxNum']
        tx["type"] = "errorEvent"
        tx["server"] = "TS1"
        tx['error'] = atr["error"]
        transaction_table.insert_one(tx)
        return tx

    if cmd == "QUOTE":
        tx['type'] = 'quoteServer'
        tx['server'] = "QS1"
        tx['stockPrice'] = data['price']
        tx['sym'] = data['sym']
        tx['cryptokey'] = data['cryptokey']
        tx['quoteServerTime'] = data['quoteServerTime']
        transaction_table.insert_one(tx)
        return tx

    if cmd == "ADD":
        tx["transactionNum"] = data['trxNum']
        tx["type"] = "accountTransaction"
        tx['server'] = "TS1"
        tx["amount"] = data['amount']
        transaction_table.insert_one(tx)
        return tx

    if cmd == "BUY" or cmd == "SELL":
        tx["transactionNum"] = data['trxNum']
        tx["type"] = "accountTransaction"
        tx['server'] = "TS1"
        tx["amount"] = data['amount']
        tx["sym"] = data['sym']
        tx['share'] = data['share']
        tx["flag"] = "pending"
        transaction_table.insert_one(tx)
        return tx
    
    if cmd in ["COMMIT_SELL","CANCEL_SELL","COMMIT_BUY","CANCEL_BUY","CANCEL_SET_SELL", "CANCEL_SET_BUY"]:
        tx["transactionNum"] = data['trxNum']
        tx["type"] = "accountTransaction"
        tx['server'] = "TS1"
        transaction_table.insert_one(tx)
        return tx
    
    if cmd in ["SET_SELL_AMOUNT","SET_SELL_TRIGGER","SET_BUY_AMOUNT","SET_BUY_TRIGGER"]:
        tx["transactionNum"] = data['trxNum']
        tx["type"] = "accountTransaction"
        tx['server'] = "TS1"
        tx["sym"] = data['sym']
        tx["amount"] = data['amount']
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
    app.run(host="0.0.0.0", debug=True)
