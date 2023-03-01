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
        update_funds = {"$set": {"funds": float(balance) + float(data['amount'])},
                        "$push": {"transactions": {
                            "timestamp":time.time(),
                            "server":"TS1",
                            "transactionNum":data['trxNum'],
                            "command":data['cmd']
                        }}}
        collection.update_one(filter, update_funds)

    for d in collection.find():
        print(d)
    return data


@app.route("/display_summary", methods=["POST"])
def display_summary():
    pass


@app.route("/buy", methods=["POST"])
def buy():
    data = request.json
    filter = {"username":data['username']}

    new_tx = {"$push": { "transactions": {
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
    collection.update_one(filter, new_tx)
    for d in collection.find():
        print(d)
    return data


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
    valid_buy = list(collection.aggregate([
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
        balance = collection.find_one({"username":data["username"]})["funds"]
        update_funds = {"$set": {"funds": float(balance) - buy_price},             
                        "$push": {"transactions": {
                            "timestamp":timestamp,
                            "server":"TS1",
                            "transactionNum":data['trxNum'],
                            "command":data['cmd']
                        }, 
                        "stocks": {"sym":stock_bought}},
                        }
        collection.update_one({"username":data["username"]}, update_funds)

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

    collection.update_one({"username":data["username"]}, new_tx)
    
    return "No valid buys"



@app.route("/cancel_buy", methods=["POST"])
def cancel_buy():
    pass


@app.route("/sell", methods=["POST"])
def sell():
    pass


@app.route("/commit_sell", methods=["POST"])
def commit_sell():
    pass


@app.route("/cancel_sell", methods=["POST"])
def cancel_sell():
    pass


@app.route("/clear", methods=["GET"])
def clear():
    collection.delete_many({})

    return "cleared DB"

if __name__ =="__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)