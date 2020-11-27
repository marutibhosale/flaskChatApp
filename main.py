from flask import Flask, render_template, request, redirect, url_for
from flask_socketio import SocketIO, join_room, leave_room
from flask_mysqldb import MySQL
from datetime import datetime
import os

app = Flask(__name__)
socketio = SocketIO(app)

# database connection
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = os.environ['user_name']
app.config['MYSQL_PASSWORD'] = os.environ['password']
app.config['MYSQL_DB'] = 'chatApp'

mysql = MySQL(app)


@app.route('/')
def home():
    """
    :return: return data from home.html file
    """

    return render_template("home.html")


@app.route('/chat')
def chat():
    """
    :return: return data from chat.html page
    """

    username = request.args.get('username')
    room = request.args.get('room')

    if username and room:
        return render_template('chat.html', username=username, room=room)
    else:
        return redirect(url_for('home'))


def create_tables():
    """ create tables is database """

    with app.app_context():
        cur = mysql.connection.cursor()
        # create user table
        cur.execute("CREATE TABLE IF NOT EXISTS user (id INT AUTO_INCREMENT PRIMARY KEY, \
                            username VARCHAR(20),room INT)")

        # create chatDetail table
        cur.execute("CREATE TABLE IF NOT EXISTS chatDetail (id INT AUTO_INCREMENT PRIMARY KEY, \
                            message TEXT, send_on DATETIME,user_id INT ,FOREIGN KEY(user_id) REFERENCES user (id))")

        mysql.connection.commit()
        cur.close()


create_tables()


@socketio.on('join_room')
def handle_join_room_event(data):
    """ for handle join room event """

    print("{} has joined the room {}".format(data['username'], data['room']))
    # joining room
    join_room(data['room'])
    # sending join room acknowledgement to client
    socketio.emit('join_room_announcement', data, room=data['room'])


@socketio.on('send_message')
def handle_send_message_event(data):
    """ for handle send message event """

    print("{} has sent message to the room {}: {}".format(data['username'],
                                                                    data['room'],
                                                                    data['message']))

    cur = mysql.connection.cursor()
    now = datetime.now()
    # extracting id from user table for current user and room
    cur.execute("SELECT id from user WHERE username=%s and room=%s", (data['username'], data['room']))
    id = cur.fetchall()

    # if current not present in database then add current user in database and message to chatDetail table
    if not id:
        table = """INSERT INTO user (username,room) VALUES (%s,%s)"""
        val = (data['username'], data['room'])
        cur.execute(table, val)
        # take last row id of user table
        user_id = cur.lastrowid
        table = """INSERT INTO chatDetail (message,send_on,user_id) VALUES (%s,%s,%s)"""
        val = (data['message'], now, user_id)
        cur.execute(table, val)
    # if current user present in database then add only message with timestamp to chatDetail table
    else:
        table = """INSERT INTO chatDetail (message,send_on,user_id) VALUES (%s,%s,%s)"""
        val = (data['message'], now, id[0][0])
        cur.execute(table, val)

    mysql.connection.commit()
    cur.close()

    socketio.emit('receive_message', data, room=data['room'])


@socketio.on('leave_room')
def handle_leave_room_event(data):
    """ for handle leave room event """

    print("{} has left the room {}".format(data['username'], data['room']))
    # leaving room after closing browser
    leave_room(data['room'])
    # sending leave room acknowledgement to client
    socketio.emit('leave_room_announcement', data, room=data['room'])


if __name__ == '__main__':
    socketio.run(app, debug=True)