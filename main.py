
from flask import Flask, render_template, request, redirect, url_for
from flask_socketio import SocketIO, join_room, leave_room

app = Flask(__name__)
socketio = SocketIO(app)


@app.route('/')
def home():
    return render_template("home.html")


if __name__ == '__main__':
    socketio.run(app, debug=True)