from flask import Flask, request
from pymongo import MongoClient
import time
import requests

client = MongoClient()
db = client.user_database
collection = db.user_table

app = Flask(__name__)

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
    # if user not in collection, create new user
    if not collection.find_one(filter):
        collection.insert_one({
            "username":data['username'],
            "funds":data['amount'],
            "stocks":[],
            "transactions":[
                {
                    "timestamp":time.time(),
                    "server":"TS1",
                    "transactionNum":data['trxNum'],
                    "command":data['cmd']
                }
            ]
        })
    # else, update existing user
    else:
        balance = collection.find_one(filter)["funds"]
        update = {"$set": {"funds": float(balance) + float(data['amount'])},
                        "$push": {"transactions": {
                            "timestamp":time.time(),
                            "server":"TS1",
                            "transactionNum":data['trxNum'],
                            "command":data['cmd']
                        }}}
        collection.update_one(filter, update)

    # for d in collection.find():
    #     print(d)
    # return data



@app.route("/display_summary", methods=["POST"])
def display_summary():
    pass


@app.route("/buy", methods=["POST"])
def buy():
    data = request.json
    filter = {"username":data['username']}

    new_buy = {"$push": { "transactions": {
            "timestamp":time.time(),
            "server":"TS1",
            "transactionNum":data['trxNum'],
            "command":data['cmd'],
            "sym": data['sym'],
            "price": data['price']  
            }
        }
    }
    # update the array of transactions to include a buy
    collection.update_one(filter, new_buy)
    for d in collection.find():
        print(d)
    return data


@app.route("/commit_buy", methods=["POST"])
def commit_buy():
    # check if a BUY command was executed in the last 60 seconds

    # if yes,
    # i) decrease funds from user
    # ii) increase stock price for symbol (or add a new stock to "stocks":[{}])
    # remove pending flag


    # else, return error
    pass


@app.route("/cancel_buy", methods=["POST"])
def cancel_buy():
    # check if a BUY command was executed in the last 60 seconds

    # if yes, cancel the transaction (remove pending flag)
    # dont add to stocks[]
    pass


@app.route("/sell", methods=["POST"])
def sell():
    # check if owned stock is >= amount being sold
    data = request.json

    # if so, call commit_sell() or cancel_sell()
    return data


@app.route("/commit_sell", methods=["POST"])
def commit_sell():
    # check if a SELL command was executed in the last 60 seconds

    # if yes,
    # i) decrease funds from user stock
    # ii) increase user funds
    pass


@app.route("/cancel_sell", methods=["POST"])
def cancel_sell():
    # check if a SELL command was executed in the last 60 seconds

    # if yes, cancel the transaction (remove pending flag)
    # dont remove from stocks[]  
    pass



if __name__ =="__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)