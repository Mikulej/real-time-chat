from flask import Flask
from flask import Flask, render_template, request, session, redirect,url_for
from flask_socketio import join_room, leave_room, send, SocketIO 
import random
from string import ascii_uppercase

import psycopg2
from config import configDatabase

def connectToDataBase():
    try:
        connection = None
        params = configDatabase()
        print("Connecting to the postgreSQL database ...")
        connection = psycopg2.connect(**params)

        #create a cursor
        cursor = connection.cursor()
        print("PostgreSQL database version: ")
        # cursor.execute('SELECT version()')
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS weather (
            city            varchar(80),
            temp_lo         int,           -- low temperature
            temp_hi         int,           -- high temperature
            prcp            real,          -- precipitation
            date            date
        );''')
        connection.commit() #commit changes
        
        # db_version = cursor.fetchone()
        # print(db_version)
        cursor.close()
    except(Exception,psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if connection is not None:
            connection.close()
            print("Database connection terminated")


def main():
    connectToDataBase()
    rooms = {}
    def generate_code(length):
        while True:
            code = ""
            for _ in range(length):
                code += random.choice(ascii_uppercase)
            if code not in rooms:
                break
        return code

    app = Flask(__name__)
    app.secret_key = 'hetman'
    socketio = SocketIO(app)
    @app.route("/",methods=["POST","GET"])
    def index():
        session.clear()
        if request.method == "POST":
            nick = request.form.get("nick")
            code = request.form.get("code")
            join = request.form.get("join", False)
            create = request.form.get("create", False)

            if not nick:
                return render_template("index.html", error="Please enter a nickname", nick=nick, code=code)
            
            if join != False and not code:
                return render_template("index.html", error="Please enter a room code", nick=nick, code=code)
            
            room = code
            if create != False:
                room = generate_code(4)
                rooms[room] = {"members": 0, "messages": []}
            elif code not in rooms:
                return render_template("index.html", error="Room does not exist", nick=nick, code=code)
            
            session["room"] = room
            session["nick"] = nick
            return redirect(url_for("room"))

        return render_template("index.html")
    

    @app.route("/room")
    def room():
        room = session.get("room")
        if room is None or session.get("nick") is None or room not in rooms:
            return redirect(url_for("index"))
        return render_template("room.html", code=room, messages=rooms[room]["messages"])
    
    @socketio.on("new_message")
    def message(data):
        room = session.get("room")
        if room not in rooms:
            return
        
        content = {
            "nick": session.get("nick"),
            "message": data["data"]
        }
        send(content, to=room)
        rooms[room]["messages"].append(content)
        print(f"{session.get('nick')} said: {data['data']}")
    
    @socketio.on("connect")
    def connect(auth):
        room = session.get("room")
        nick = session.get("nick")
        if not room or not nick:
            return
        if room not in rooms:
            leave_room(room)
            return
        
        join_room(room)
        send({"nick":nick,"message": "has entered the room"}, to=room)
        rooms[room]["members"] += 1
        print(f"{nick} has joined room {room}")

    @socketio.on("disconnect")
    def disconnect():
        room = session.get("room")
        nick = session.get("nick")
        leave_room(room)

        if room in rooms:
            rooms[room]["members"] -= 1
            if rooms[room]["members"] <= 0:
                del rooms[room]

        send({"nick":nick,"message": "has left the room"}, to=room)
        print(f"{nick} has left room {room}")
    
    #app.run()
    socketio.run(app,debug=True)

    
    return

if __name__ == "__main__":
    
    main()