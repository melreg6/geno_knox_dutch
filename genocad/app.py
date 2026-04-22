from flask import Flask, render_template, request
from dotenv import load_dotenv
import os
import mysql.connector

load_dotenv()

app = Flask(__name__)

def get_db_connection():
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password=os.getenv("MYSQL_PASSWORD"),
        database="genocad"
    )
    return conn

@app.route('/')
def index():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SHOW TABLES")
    tables = [list(row.values())[0] for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return render_template('index.html', tables=tables)

@app.route('/table/<table_name>')
def view_table(table_name):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(f"SELECT * FROM `{table_name}` LIMIT 50")  # limit for performance
    rows = cursor.fetchall()
    cursor.execute(f"SHOW COLUMNS FROM `{table_name}`")
    columns = [col['Field'] for col in cursor.fetchall()]
    cursor.close()
    conn.close()
    return render_template('table.html', table_name=table_name, columns=columns, rows=rows)

if __name__ == '__main__':
    app.run(debug=True)