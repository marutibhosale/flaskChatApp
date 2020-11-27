
from flask import Flask, render_template, request, redirect, url_for
from flask_socketio import SocketIO, join_room, leave_room
from flask_mysqldb import MySQL
import os
from datetime import datetime

app = Flask(__name__)
socketio = SocketIO(app)


app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'root'
app.config['MYSQL_DB'] = 'chatApp'

mysql = MySQL(app)


@app.route('/')
def home():
    return render_template("home.html")

@app.route('/chat')
def chat():
    username = request.args.get('username')
    room = request.args.get('room')

    if username and room:
        return render_template('chat.html', username=username, room=room)
    else:
        return redirect(url_for('home'))

def create_tables():
    with app.app_context():
        cur = mysql.connection.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS user (id INT AUTO_INCREMENT PRIMARY KEY, \
                            username VARCHAR(20),room INT)")

        cur.execute("CREATE TABLE IF NOT EXISTS chatDetail (id INT AUTO_INCREMENT PRIMARY KEY, \
                            message TEXT, send_on DATETIME,user_id INT ,FOREIGN KEY(user_id) REFERENCES user (id))")

        mysql.connection.commit()
        cur.close()


create_tables()

@socketio.on('join_room')
def handle_join_room_event(data):
    print("{} has joined the room {}".format(data['username'], data['room']))
    join_room(data['room'])
    socketio.emit('join_room_announcement', data, room=data['room'])


@socketio.on('send_message')
def handle_send_message_event(data):
    print("{} has sent message to the room {}: {}".format(data['username'],
                                                                    data['room'],
                                                                    data['message']))

    cur = mysql.connection.cursor()
    now = datetime.now()
    cur.execute("SELECT id from user WHERE username=%s and room=%s", (data['username'], data['room']))
    id = cur.fetchall()

    if str(id) == '()':
        table = """INSERT INTO user (username,room) VALUES (%s,%s)"""
        val = (data['username'], data['room'])
        cur.execute(table, val)
        user_id = cur.lastrowid
        table = """INSERT INTO chatDetail (message,send_on,user_id) VALUES (%s,%s,%s)"""
        val = (data['message'], now, user_id)
        cur.execute(table, val)
    else:
        table = """INSERT INTO chatDetail (message,send_on,user_id) VALUES (%s,%s,%s)"""
        val = (data['message'], now, id[0][0])
        cur.execute(table, val)

    mysql.connection.commit()
    cur.close()

    socketio.emit('receive_message', data, room=data['room'])

@socketio.on('leave_room')
def handle_leave_room_event(data):
    print("{} has left the room {}".format(data['username'], data['room']))
    leave_room(data['room'])
    socketio.emit('leave_room_announcement', data, room=data['room'])


if __name__ == '__main__':
    socketio.run(app, debug=True)