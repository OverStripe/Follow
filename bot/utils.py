import random
import string
import sqlite3

def save_account(email, username, password):
    conn = sqlite3.connect("database/accounts.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO accounts (email, username, password) VALUES (?, ?, ?)", (email, username, password))
    conn.commit()
    conn.close()

def fetch_accounts():
    conn = sqlite3.connect("database/accounts.db")
    cursor = conn.cursor()
    cursor.execute("SELECT username FROM accounts")
    accounts = cursor.fetchall()
    conn.close()
    return accounts

def generate_username():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))

def generate_password():
    return ''.join(random.choices(string.ascii_letters + string.digits + "!@#$%^&*", k=12))
  
