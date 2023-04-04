from flask import Flask, request, jsonify
from pymongo import MongoClient
import xml.etree.ElementTree as ET
import xml.dom.minidom
import time
import requests
import redis
import json 
from flask_cors import CORS
from userutilsservice import test, recent_transaction, new_transaction, account_exists, quote, get_quote

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


@app.route("/sell", methods=["POST"])
def sell():
    data = request.json
    # check if account exists
    if not account_exists(data['username']):
        return str(new_transaction(data, error="The specified user does not exist."))

    filter = {"username":data['username']}

    # get the quote (automatically updates user stock)
    stock_quote = quote(data['sym'], data['username']).json
    stock_price = stock_quote['price']

    # share that can be bought with the specified price rounded to the nearest whole number
    share = float(data['amount']) // float(stock_price)
    data['share'] = share

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
        new_share = recent_tx['share']

        # subtract stock amount
        stock_filter = {"username": data['username'], "stocks.sym": stock}
        amount_owned = user_table.find_one(stock_filter, {"stocks.$": 1})['stocks'][0]['amount']

        # subtract share
        share = user_table.find_one(stock_filter, {"stocks.$": 1})['stocks'][0]['share']
        user_table.update_one(stock_filter, {"$set": {"stocks.$.amount": float(amount_owned) - float(price), 
                                                      "stocks.$.share": float(share) - float(new_share)}} )

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



@app.route("/set_sell_amount", methods=["POST"])
def set_sell_amount():
    data = request.json
    filter = {'username':data['username']}

    if not account_exists(data['username']):
        new_transaction(data, error="The specified user does not exist.")
    
    # check if the user has the amount of stock
    valid_stock = user_table.find_one({'username': data['username'], 'stocks.sym': data['sym'], 'stocks.amount': {'$gte': data['amount']}})

    if not valid_stock:
        new_transaction(data, error="Not enough stock.")
        return "Not enough stock owned to SET_SELL_AMOUNT"

    # add to reserved sell
    user_table.update_one(filter, {"$push": {"transactions": new_transaction(data), 
                                             "reserved_sell": {'sym':data['sym'], 'amount':data['amount'] , 'trigger':""}}})
    return 'Set Sell Amount'



@app.route("/set_sell_trigger", methods=["POST"])
def set_sell_trigger():
    data = request.json
    filter = {'username':data['username']}

    if not account_exists(data['username']):
        new_transaction(data, error="The specified user does not exist.")

    # check if the sell amount has been set in reserved_sell[]
    valid_trigger = user_table.find_one({'username': data['username'], 'reserved_sell.sym': data['sym']})

    if not valid_trigger:
        new_transaction(data, error="Set sell amount first.")
        return "Set sell amount first."
    
    user_table.update_one({'username': data['username'], 'reserved_sell.sym': data['sym']}, {'$set': {'reserved_sell.$.trigger': data['amount']}})

    # subtract stock amount and share from owned stock
    sell_point = data['amount']
    stock_filter = {"username": data['username'], "stocks.sym": data['sym']}
    reserved_filter = {"username": data['username'], "reserved_sell.sym": data['sym']}
    amount_to_sell = user_table.find_one(reserved_filter, {"reserved_sell.$": 1})['reserved_sell'][0]['amount']
    amount_owned = user_table.find_one(stock_filter, {"stocks.$": 1})['stocks'][0]['amount']
    share_owned = user_table.find_one(stock_filter, {"stocks.$": 1})['stocks'][0]['share']
    share_subtracted = float(amount_to_sell) // float(sell_point)

    # update user stocks[]
    user_table.update_one(stock_filter, {"$set": {"stocks.$.amount": float(amount_owned) - float(amount_to_sell), 
                                                  "stocks.$.share": float(share_owned) - float(share_subtracted)}} )

    # add trigger to reserved_sell
    user_table.update_one(reserved_filter, {"$set": {"reserved_sell.$.trigger": sell_point}})

    # add to transactions
    user_table.update_one(filter, {"$push": { "transactions": new_transaction(data)}})
    return "Set Sell Trigger"



@app.route("/cancel_set_sell", methods=["POST"])
def cancel_set_sell():
    data = request.json

    if not account_exists(data['username']):
        new_transaction(data, error="The specified user does not exist.")
    
    filter = {"username":data['username']}
    reserved_filter = {"username": data['username'], "reserved_sell.sym": data['sym']}

    valid_reserve = user_table.find_one(reserved_filter, {"reserved_sell.$": 1})

    if not valid_reserve:
        new_transaction(data, error="No prereq SET_SELL_AMOUNT")
        return f"No prereq SET_SELL_AMOUNT for stock {data['sym']}"
    
    # add back stock amount and share to owned stock
    stock_filter = {"username": data['username'], "stocks.sym": data['sym']}
    amount_to_sell = user_table.find_one(reserved_filter, {"reserved_sell.$": 1})['reserved_sell'][0]['amount']
    trigger = user_table.find_one(reserved_filter, {"reserved_sell.$": 1})['reserved_sell'][0]['trigger']
    amount_owned = user_table.find_one(stock_filter, {"stocks.$": 1})['stocks'][0]['amount']
    share_owned = user_table.find_one(stock_filter, {"stocks.$": 1})['stocks'][0]['share']
    if trigger != "":
        share_subtracted = float(amount_to_sell) // float(trigger)
        # update user stocks
        user_table.update_one(stock_filter, {"$set": {"stocks.$.amount": float(amount_owned) + float(amount_to_sell), 
                                                  "stocks.$.share": float(share_owned) + float(share_subtracted)}} )
    # remove from reserved_sell
    user_table.update_one(reserved_filter, {"$pull": {"reserved_sell": {"sym": data['sym']}}})
    
    # add a transaction
    user_table.update_one(filter, {"$push": { "transactions": new_transaction(data)}})

    return 'Cancelled Set Sell'


@app.route("/testing", methods=["GET"])
def testing():
    return "ITS WORKING FROM SELL"


@app.route("/testing_userutils", methods=["GET"])
def testing_userutils():
    return test()


if __name__ =="__main__":
    app.run(host="0.0.0.0", debug=True)
