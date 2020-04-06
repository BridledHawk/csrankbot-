import sqlite3
conn = sqlite3.connect('users.db')
c = conn.cursor()
c.execute('''CREATE TABLE users
             (discordID text UNIQUE NOT NULL, steamID text UNIQUE NOT NULL)''')
conn.commit()
conn.close()
