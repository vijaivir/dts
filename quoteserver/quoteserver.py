from flask import Flask, jsonify
# from pyngrok import ngrok
import random

# ngrok.set_auth_token("2MNvxD4C2f6zFT3cyIJJPJUg46K_7soQMKgoMqZFvGhsAMSXo")
# public_url = ngrok.connect(5000).public_url
# print("PUBLIC URL:", public_url)
# port_no = 5000
app = Flask(__name__)


share_price = None
@app.route("/quote", methods=["GET", "POST"])
def quote():
    global share_price

    if share_price is None:
        share_price = random.uniform(20.0,50.0)
        res = {
            "price": "%.2f" % share_price
        }
        return jsonify(res)

    share_changed = random.choice([0,1])
    if share_changed == 1:
        # stock price increased
        share_price += random.uniform(0.0, share_price*0.35)
    else:
        # stock price decreased
        share_price -= random.uniform(0.0, share_price*0.15)
    res = {
        "price": "%.2f" % share_price,
        "cryptokey": "1wb2DqmVTnPYxw6fNtql5qKYkEQ"
    }
    return jsonify(res)


if __name__ == "__main__":
    app.run(port=5000)