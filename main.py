from flask import Flask, render_template, request, url_for,redirect, session
from flask_socketio import SocketIO

from database import Database

import random
import string

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
        text            varchar(30),           
        date            timestamp,
        CONSTRAINT fk_user         
            FOREIGN KEY(user_id) 
               REFERENCES accounts(id)
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
                
            #return render_template("home.html", username=username)
            session["username"] = username
            return redirect("/home")
            

            #if register != False and username == False or password == False:
        return render_template("index.html")
    
    def generate_code(length: int) -> string:
        return ''.join(random.choice(string.ascii_uppercase) for _ in range(length))
        
    @app.route("/home",methods=["POST","GET"])
    def home():
        username = session["username"]
        if username == None :
            return redirect("/")
        createRoom = request.form.get("createRoom",False)
        joinRoom = request.form.get("register",False)
        roomCode = request.form.get("roomCode",False)
        #get rooms
        db.execute("SELECT * FROM accounts WHERE username=\'{0}\';".format(username))
        user = db.fetchone() 
        user_id = user[0]
        db.execute("SELECT user_id,room_id,code FROM members JOIN rooms ON id= room_id WHERE user_id=\'{0}\';".format(user_id))
        user_rooms_raw = db.fetchall() 
        #TO DO: return list of rooms
        
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

            return render_template("home.html", username=session["username"])
        return render_template("home.html", username=session["username"])
    
    
    
    socketio.run(app)
    db.disconnect()
    

if __name__ == '__main__':
    main()

