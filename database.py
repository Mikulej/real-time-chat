import psycopg2
from config import configDatabase

class Database:
    def __init__(self):    
        self.connection = None

    def connect(self):
        try:
            params = configDatabase()
            self.connection = psycopg2.connect(**params)
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
            cursor = self.connection.cursor()
            cursor.execute(query)
            self.connection.commit()
        except(Exception,psycopg2.DatabaseError) as error:
            print(error) 
        