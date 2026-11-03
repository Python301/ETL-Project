import pyodbc
from config import CONNECTION_STRING_Source

try:

    conn = pyodbc.connect(CONNECTION_STRING_Source)

    print("SQL Server Connected Successfully!")

    cursor = conn.cursor()

    # cursor.execute("SELECT * FROM Employees")
    cursor.execute("SELECT @@SERVERNAME, DB_NAME()")
    result = cursor.fetchall()

    print("result:", result)
    #print("Database:", result[1])

    conn.close()

except Exception as e:

    print("Connection Failed:", e)
