import pyodbc
import pandas as pd
from config import CONNECTION_STRING_Target, CONNECTION_STRING_Source
import schedule
import time

def SourceDBGetData(last_watermark):
    # Connect to SourceDB
    conn = pyodbc.connect(CONNECTION_STRING_Source)

    select_query = """
    SELECT
        EmployeeID,
        EmployeeName,
        Department,
        Salary,
        ModifiedDate
    FROM SourceDB.dbo.Employees
    WHERE ModifiedDate > ?
    ORDER BY ModifiedDate;
    """
    # Pass watermark as a parameter
    df = pd.read_sql_query(
        select_query,
        conn,
        params=[last_watermark]
    )
    print("SourceDB records:", len(df))
    return df

# def TargetDBInsert(df):
#     # Connect to SQL Server
#     conn = pyodbc.connect(CONNECTION_STRING_Target)
#     cursor = conn.cursor()
#     # 3. Insert data into TargetDB
#     if not df.empty:
#         insert_query = """
#         INSERT INTO TargetDB.dbo.Employees
#         (
#             EmployeeID,
#             EmployeeName,
#             Department,
#             Salary,
#             ModifiedDate
#         )
#         VALUES (?, ?, ?, ?, ?);
#         """

#         records = list(
#             df.itertuples(index=False, name=None)
#         )

#         cursor.fast_executemany = True
#         cursor.executemany(insert_query, records)

#         conn.commit()
#         return df["ModifiedDate"].max()

#         print("Data inserted successfully!")

#     else:
#         print("No records found in SourceDB.")


def TargetDBInsert(df):

    if df.empty:
        print("No records found in SourceDB.")
        return None

    conn = None
    cursor = None

    try:
        # Connect to TargetDB
        conn = pyodbc.connect(CONNECTION_STRING_Target)
        cursor = conn.cursor()

        # Create temporary staging table
        cursor.execute("""
            CREATE TABLE #Employees_Staging
            (
                EmployeeID INT,
                EmployeeName VARCHAR(100),
                Department VARCHAR(50),
                Salary DECIMAL(10,2),
                ModifiedDate DATETIME2(7)
            );
        """)

        # Insert extracted records into staging table
        insert_query = """
            INSERT INTO #Employees_Staging
            (
                EmployeeID,
                EmployeeName,
                Department,
                Salary,
                ModifiedDate
            )
            VALUES (?, ?, ?, ?, ?);
        """

        records = list(
            df.itertuples(index=False, name=None)
        )

        cursor.fast_executemany = True
        cursor.executemany(insert_query, records)

        # Update existing employees and insert new employees
        merge_query = """
            MERGE INTO dbo.Employees AS Target
            USING #Employees_Staging AS Source
                ON Target.EmployeeID = Source.EmployeeID

            WHEN MATCHED THEN
                UPDATE SET
                    Target.EmployeeName = Source.EmployeeName,
                    Target.Department = Source.Department,
                    Target.Salary = Source.Salary,
                    Target.ModifiedDate = Source.ModifiedDate

            WHEN NOT MATCHED BY TARGET THEN
                INSERT
                (
                    EmployeeID,
                    EmployeeName,
                    Department,
                    Salary,
                    ModifiedDate
                )
                VALUES
                (
                    Source.EmployeeID,
                    Source.EmployeeName,
                    Source.Department,
                    Source.Salary,
                    Source.ModifiedDate
                );
        """

        cursor.execute(merge_query)

        conn.commit()

        print("Data inserted/updated successfully!")

        return df["ModifiedDate"].max()

    except Exception as e:
        if conn:
            conn.rollback()

        print("TargetDB Error:", e)
        raise

    finally:
        if cursor:
            cursor.close()

        if conn:
            conn.close()


def UpdateWatermark(new_watermark):

    if new_watermark is None:
        return

    conn = None
    cursor = None

    try:
        conn = pyodbc.connect(CONNECTION_STRING_Target)
        cursor = conn.cursor()

        update_query = """
        UPDATE dbo.ETL_Watermark
        SET LastModifiedDate = ?
        WHERE PipelineName = 'Employee_ETL';
        """

        cursor.execute(update_query, new_watermark)

        if cursor.rowcount == 0:
            raise Exception("Watermark record not found!")

        conn.commit()

        print("Watermark updated:", new_watermark)

    except Exception:
        if conn:
            conn.rollback()
        raise

    finally:
        if cursor:
            cursor.close()

        if conn:
            conn.close()

def main():
    # Connect to SQL Server
    conn = pyodbc.connect(CONNECTION_STRING_Target)
    cursor = conn.cursor()
    # Read watermark
    cursor.execute("""
        SELECT LastModifiedDate
        FROM dbo.ETL_Watermark
        WHERE PipelineName = 'Employee_ETL'
    """)

    result = cursor.fetchone()
    if result is None:
        raise Exception("Watermark record not found!")
    last_watermark = result[0]
    print("Last Watermark:", last_watermark)

    # Get data from SourceDB
    df = SourceDBGetData(last_watermark)
    print(df)

    WMD = TargetDBInsert(df)
    print("WMD:", WMD)

    UpdateWatermark(WMD)

# if __name__ == "__main__":
#     main()



def job():
    print("ETL job started")
    main()
    print("ETL job completed")
# Run every 1 minute
schedule.every(1).minutes.do(job)

# Run the scheduler continuously
while True:
    schedule.run_pending()
    time.sleep(10)
