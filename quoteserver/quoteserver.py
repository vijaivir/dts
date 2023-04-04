from flask import Flask, jsonify
import random

app = Flask(__name__)

share_price = None
@app.route("/quoteserver/quote", methods=["GET", "POST"])
def quote():
    global share_price

    if share_price is None:
        share_price = random.uniform(20.0,50.0)
        res = {
            "price": "%.2f" % share_price,
            "cryptokey": "1wb2DqmVTnPYxw6fNtql5qKYkEQ"
        }
        return jsonify(res)

    share_changed = random.choice([0,1])
    if share_changed == 1:
        # stock price increased
        share_price += random.uniform(0.0, share_price*0.15)
    else:
        # stock price decreased
        share_price -= random.uniform(0.0, share_price*0.15)
        if share_price < 0.01:
            share_price = 0.01
    res = {
        "price": "%.2f" % share_price,
        "cryptokey": "1wb2DqmVTnPYxw6fNtql5qKYkEQ"
    }
    return jsonify(res)


if __name__ == "__main__":
    app.run(host="0.0.0.0")