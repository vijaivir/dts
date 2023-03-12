from flask import Flask, request
app = Flask(__name__)

@app.route("/buy", methods=["GET"])
def buy():
    return "This is a buy service"



if __name__ == "__main__":
    app.run(debug=True, port=8080, host='0.0.0.0')