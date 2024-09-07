from flask import Flask, render_template, request, url_for,redirect, session
from flask_socketio import SocketIO, join_room, leave_room

from database import Database

import random
import string
import datetime

def main():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'secret!'
    socketio = SocketIO(app)

    # Database Initilization ----------------------------
    db: Database = Database()
    db.connect()
    db.execute('''CREATE TABLE IF NOT EXISTS accounts (
        username        varchar(10),
        password        varchar(30),           
        id              BIGSERIAL PRIMARY KEY
    );''')

    db.execute('''CREATE TABLE IF NOT EXISTS rooms (
        id              BIGSERIAL PRIMARY KEY,
        code            varchar(4)      
    );''')

    db.execute('''CREATE TABLE IF NOT EXISTS members (
        user_id         BIGSERIAL,
        room_id         BIGSERIAL,
        role            INT,
        CONSTRAINT fk_user         
            FOREIGN KEY(user_id) 
               REFERENCES accounts(id),
        CONSTRAINT fk_room         
            FOREIGN KEY(room_id) 
               REFERENCES rooms(id)           
    );''')

    db.execute('''CREATE TABLE IF NOT EXISTS messages (
        user_id         BIGSERIAL,
        room_id         BIGSERIAL,
        text            varchar(100),           
        date            timestamp,
        CONSTRAINT fk_user         
            FOREIGN KEY(user_id) 
               REFERENCES accounts(id),
        CONSTRAINT fk_room         
            FOREIGN KEY(room_id) 
               REFERENCES rooms(id)      
    );''')

    # Flask route ----------------------------

    @app.route("/",methods=["POST","GET"])
    def index():
        session.clear()
        session["username"] = None
        if request.method == "POST":
            username = request.form.get("username",False)
            password = request.form.get("password",False)
            login = request.form.get("login",False)
            register = request.form.get("register",False)

            if register != False:
                if len(username) > 10 or len(username) < 4:
                    return render_template("index.html", username=username,error="Invalid username length (username must be between 4 and 10 characters long)")
                if len(password) > 30 or len(password) < 4:
                    return render_template("index.html", username=username,error="Invalid password length (password must be between 4 and 30 characters long)")
                
                db.execute("SELECT * FROM accounts WHERE username=\'{0}\';".format(username))
                if db.fetchone() != None:
                    return render_template("index.html", username=username,error="Username already taken")

                db.execute("INSERT INTO accounts (username,password) VALUES (\'{0}\',\'{1}\')".format(username,password))

                return render_template("index.html",error="Registration complete, please log in")
                
            if login != False and username != False and password != False:
                if len(username) > 10 or len(username) < 4:
                    return render_template("index.html", username=username,error="Wrong username or password")
                if len(password) > 30 or len(password) < 4:
                    return render_template("index.html", username=username,error="Wrong username or password")
                
                #check if username exsists          
                db.execute("SELECT * FROM accounts WHERE username=\'{0}\';".format(username))
                row = db.fetchone() 
                if row == None:
                    return render_template("index.html", username=username,error="Wrong username or password")
                #check if password is correct
                if row[1] != password:
                    return render_template("index.html", username=username,error="Wrong username or password")
                #store user_id in session
                session["user_id"] = row[2]
                
            session["username"] = username
            
            return redirect("/home")

        return render_template("index.html")
    
    def generate_code(length: int) -> string:
        return ''.join(random.choice(string.ascii_uppercase) for _ in range(length))
    
    @app.route("/home",methods=["POST","GET"])
    def home():
        username = session["username"]
        if username == None :
            return redirect("/")
        createRoom = request.form.get("createRoom",False)
        joinRoom = request.form.get("joinRoom",False)
        roomCode = request.form.get("roomCode",False)
        availableRoom = request.form.get("availableRoom",False)

        #if selected a room, go to that room
        if availableRoom != False:
            session["roomCode"] = availableRoom
            #store room_id in session
            db.execute("SELECT * FROM rooms WHERE code=\'{0}\';".format(availableRoom))
            row = db.fetchone() 
            session["room_id"] = row[0]
            return redirect(url_for("room",code=availableRoom))
        #get rooms
        db.execute("SELECT * FROM accounts WHERE username=\'{0}\';".format(username))
        user = db.fetchone() 
        user_id = user[2]
        db.execute("SELECT user_id,room_id,code FROM members JOIN rooms ON id= room_id WHERE user_id=\'{0}\';".format(user_id))
        user_rooms_raw = db.fetchall() 

        if joinRoom != False:
            if roomCode == "":
                return render_template("home.html", username=session["username"],rooms=user_rooms_raw, error="Enter the code of the room")
            db.execute("SELECT * FROM rooms WHERE code=\'{0}\';".format(roomCode))
            row = db.fetchone() 
            if row == None:
                return render_template("home.html", username=session["username"],rooms=user_rooms_raw, error="Room '\'{0}'\' does not exsists".format(roomCode))
            #check if this user is already a member of this room
            room_id = row[0]
            db.execute("SELECT * FROM members WHERE user_id=\'{0}\' AND room_id=\'{1}\';".format(user_id,room_id))
            row = db.fetchone() 
            if row != None:
                return render_template("home.html", username=session["username"],rooms=user_rooms_raw, error="You are already a member of room '\'{0}'\'".format(roomCode))
            #add user as a member to that room    
            db.execute("INSERT INTO members (user_id,room_id,role) VALUES (\'{0}\',\'{1}\',\'{2}\')".format(user_id,room_id,0))
        
        if createRoom != False:
            #check if room with that code exsists
            generateNewCode = True
            while generateNewCode:
                code = generate_code(4)
                db.execute("SELECT * FROM rooms WHERE code=\'{0}\';".format(code))
                row = db.fetchone() 
                if row == None:
                    generateNewCode = False
            db.execute("INSERT INTO rooms (code) VALUES (\'{0}\')".format(code))
            #get id of new room     
            db.execute("SELECT * FROM rooms WHERE code=\'{0}\';".format(code))
            row = db.fetchone() 
            room_id = row[0]
            #get id of user
            db.execute("SELECT * FROM accounts WHERE username=\'{0}\';".format(username))
            row = db.fetchone() 
            user_id = row[2]
            #add account that created a room as a member of that room
            db.execute("INSERT INTO members (user_id,room_id,role) VALUES (\'{0}\',\'{1}\',\'{2}\')".format(user_id,room_id,3))
            #get rooms
            db.execute("SELECT * FROM accounts WHERE username=\'{0}\';".format(username))
            user = db.fetchone() 
            user_id = user[2]
            db.execute("SELECT user_id,room_id,code FROM members JOIN rooms ON id= room_id WHERE user_id=\'{0}\';".format(user_id))
            user_rooms_raw = db.fetchall() 
            return render_template("home.html", username=session["username"],rooms=user_rooms_raw)
        return render_template("home.html", username=session["username"],rooms=user_rooms_raw)
    
    @app.route("/room/<code>",methods=["POST","GET"])
    def room(code):
        username = session["username"]
        roomCode = session["roomCode"]
        if username == None or roomCode == None:
            return redirect("/")

        db.execute("SELECT * FROM (SELECT accounts.username,messages.text,messages.date FROM messages JOIN accounts ON messages.user_id=accounts.id WHERE room_id={0} ORDER BY date DESC LIMIT {1}) ORDER BY date ASC;".format(session.get("room_id"),10))
        messages = db.fetchall()
        
        return render_template("room.html",code=code,username=username,messages=messages)
    
    # Flask socketio ----------------------------
    @socketio.on("connect")
    def connect(auth):
        username = session.get("username")
        code = session.get("roomCode")
        join_room(code)

    @socketio.on('disconnect')
    def disconnect():
        username = session.get("username")
        code = session.get("roomCode")
        leave_room(code)


    @socketio.on('sendMessage')
    def sendMessage(data):
        code = session.get("roomCode")

        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        db.execute("INSERT INTO messages (user_id,room_id,text,date) VALUES (\'{0}\',\'{1}\',\'{2}\',\'{3}\')".format(session.get("user_id"),
                                                                                                                      session.get("room_id"),
                                                                                                                      data["message"],
                                                                                                                      current_time))
        data["datetime"] = current_time
        socketio.send(data=data,to=code)

    socketio.run(app)
    db.disconnect()
    

if __name__ == '__main__':
    main()

