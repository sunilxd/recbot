from flask import Flask
from threading import Thread

app = Flask(__name__)

@app.route("/")
def hello_world():
    return "<p>I am live!</p>"


def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()
    return t
