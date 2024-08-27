from flask import Flask, render_template, request
from flask_socketio import SocketIO

from database import Database

    

def main():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'secret!'
    socketio = SocketIO(app)

    db: Database = Database()
    db.connect()
    db.execute('''CREATE TABLE IF NOT EXISTS accounts (
        username        varchar(10),
        password        varchar(30),           
        id              BIGSERIAL PRIMARY KEY
    );''')

    # Database.execute(db,query=
    # '''CREATE TABLE IF NOT EXISTS messages (
    #     code            varchar(4),
    #     nick            varchar(20),           
    #     message         varchar(100),                   
    #     date            timestamp
    # );''')
    

    @app.route("/",methods=["POST","GET"])
    def index():
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
                
            
            

            #if register != False and username == False or password == False:
           


            
        return render_template("index.html")
    
    
    socketio.run(app)
    db.disconnect()
    

if __name__ == '__main__':
    main()

