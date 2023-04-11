from flask import Flask, request, jsonify
from pymongo import MongoClient
import xml.etree.ElementTree as ET
import xml.dom.minidom
import time
import requests
import redis
import json
from flask_cors import CORS
from userutilsservice import test, recent_transaction, new_transaction, account_exists, quote

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
CORS(app)



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
    stock_quote = quote(data['sym'], data['username']).json
    
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



@app.route("/testing", methods=["GET"])
def testing():
    return 'TESTING FROM BUYSERICE'

@app.route("/testing_userutils", methods=["GET"])
def testing_userutils():
    return test()

if __name__ =="__main__":
    app.run(host="0.0.0.0", debug=True)