from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room
import random
import math
import threading
import time

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

GAME_TIME = 60

rooms = {}
user_sessions = {}

@app.route("/")
def home():
    return render_template("index.html")


# ---------------- TIMER ----------------

def game_timer(room):

    for i in range(GAME_TIME, -1, -1):

        if room not in rooms:
            return

        rooms[room]["time"] = i
        socketio.emit("timer_update", i, room=room)

        time.sleep(1)

    players = rooms[room]["players"]

    if players:
        winner = max(players, key=players.get)

        socketio.emit(
            "game_over",
            {"winner": winner, "scores": players},
            room=room
        )

    rooms[room]["game_started"] = False


# ---------------- JOIN ROOM ----------------

@socketio.on("join_room")
def join(data):

    name = data["name"]
    room = data["room"]
    sid = request.sid

    join_room(room)

    user_sessions[sid] = {
        "name": name,
        "room": room
    }

    if room not in rooms:

        rooms[room] = {
            "players": {},
            "hidden": {
                "x": random.randint(50,450),
                "y": random.randint(50,450)
            },
            "time": GAME_TIME,
            "game_started": False
        }

    rooms[room]["players"][name] = rooms[room]["players"].get(name,0)

    emit("update_players", rooms[room]["players"], room=room)

    emit("timer_update", rooms[room]["time"])


# ---------------- START GAME ----------------

@socketio.on("start_game")
def start(data):

    room = data["room"]

    if not rooms[room]["game_started"]:

        rooms[room]["game_started"] = True

        threading.Thread(
            target=game_timer,
            args=(room,)
        ).start()


# ---------------- PLAYER CLICK ----------------

@socketio.on("click_position")
def click(data):

    name = data["name"]
    room = data["room"]
    x = data["x"]
    y = data["y"]

    if not rooms[room]["game_started"]:
        return

    hidden = rooms[room]["hidden"]

    dx = x - hidden["x"]
    dy = y - hidden["y"]

    distance = math.sqrt(dx*dx + dy*dy)

    emit("click_effect", {"x":x,"y":y,"player":name}, room=room)

    if distance < 30:

        rooms[room]["players"][name] += 1

        rooms[room]["hidden"] = {
            "x": random.randint(50,450),
            "y": random.randint(50,450)
        }

        emit("update_players", rooms[room]["players"], room=room)

        emit("game_message", f"{name} found it! 🎉", room=room)

    else:

        memes = [
            "😂 Aim.exe stopped",
            "💀 Not even close",
            "🐒 Monkey aim activated",
            "🚀 Wrong galaxy",
            "🤣 Try again",
            "My life is joke.😅",
            "Social battery: very low.😅",
            "Expectations versus reality. Agree?😅",
            "🧠 Brain buffering... try again!",
            "🎯 Target escaped your aim!",
            "😅 Nice try, but nope!",
            "My life is joke.😅",
            "Social battery: very low.😅",
            "Expectations versus reality. Agree?😅",
            "🧠 Brain buffering... try again!",
            "🎯 Target escaped your aim!",
            "😅 Nice try, but nope!"
        ]

        emit("game_message", random.choice(memes), room=room)


# ---------------- CHAT ----------------

@socketio.on("chat_message")
def chat(data):

    room = data["room"]
    name = data["name"]
    msg = data["msg"]

    emit("chat_message", f"{name}: {msg}", room=room)


# ---------------- DISCONNECT ----------------

@socketio.on("disconnect")
def disconnect():

    sid = request.sid

    if sid not in user_sessions:
        return

    name = user_sessions[sid]["name"]
    room = user_sessions[sid]["room"]

    del user_sessions[sid]

    if room in rooms and name in rooms[room]["players"]:

        del rooms[room]["players"][name]

        socketio.emit(
            "update_players",
            rooms[room]["players"],
            room=room
        )


if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000)