import mysql.connector
import pandas as pd
import os
from dotenv import load_dotenv
load_dotenv()

conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password=os.getenv("MYSQL_PASSWORD"),
    database="genocad"
)

df = pd.read_sql("SELECT * FROM categories", conn)

print(df.head())