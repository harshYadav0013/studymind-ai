from backend.database import get_connection

connection = get_connection()

cursor = connection.cursor()

cursor.execute("SHOW TABLES")

tables = cursor.fetchall()

for table in tables:
    print(table[0])

cursor.close()
connection.close()
