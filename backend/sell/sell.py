from flask import Flask, request
app = Flask(__name__)

@app.route("/sell", methods=["GET"])
def sell():
    return "This is a selling service"


if __name__ == "__main__":
    app.run(debug=True, port=8080, host='0.0.0.0')