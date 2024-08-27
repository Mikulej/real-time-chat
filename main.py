from flask import Flask, render_template, request
from flask_socketio import SocketIO

from database import Database

    

def main():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'secret!'
    socketio = SocketIO(app)

    db: Database = Database
    Database.connect(db)
    Database.execute(db,query=
    '''CREATE TABLE IF NOT EXISTS messages (
        code            varchar(4),
        nick            varchar(20),           
        message         varchar(100),                   
        date            timestamp
    );''')
    Database.disconnect(db)

    @app.route("/",methods=["POST","GET"])
    def index():
        if request.method == "POST":
            username = request.form.get("username",False)
            password = request.form.get("password",False)
            login = request.form.get("login",False)
            register = request.form.get("register",False)

            if login != False:
                if len(username) > 10:
                    return render_template("index.html", username=username,error="Username too long (Exceeded 10 characters)")
                return render_template("index.html",error="Login ok")
                
            
            

            #if register != False and username == False or password == False:
           


            
        return render_template("index.html")

    socketio.run(app)

if __name__ == '__main__':
    main()

