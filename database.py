import psycopg2
from config import configDatabase

class Database:
    def __init__(self):    
        self.connection = None
        self.cursor = None

    def connect(self):
        try:
            params = configDatabase()
            self.connection = psycopg2.connect(**params)
            self.cursor = self.connection.cursor()
            print("Succesfully connected to database.")
        except(Exception,psycopg2.DatabaseError) as error:
            print(error) 

    def disconnect(self):
        try:
            if self.connection is not None:
                self.connection.close()
                print("Database connection terminated")
        except(Exception,psycopg2.DatabaseError) as error:
            print(error) 

    def execute(self,query):
        try:
            
            self.cursor.execute(query)
            self.connection.commit()
        except(Exception,psycopg2.DatabaseError) as error:
            print(error) 

    def fetchone(self):
        try:
            return self.cursor.fetchone()
        except(Exception,psycopg2.DatabaseError) as error:
            print(error) 

    def fetchall(self):
        try:
            return self.cursor.fetchall()
        except(Exception,psycopg2.DatabaseError) as error:
            print(error) 

        