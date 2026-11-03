
SERVER = r"localhost\SQLEXPRESS"

SOURCE_DB = "SourceDB"
TARGET_DB = "TargetDB"

DRIVER = "ODBC Driver 17 for SQL Server"

CONNECTION_STRING_Source = (
    f"DRIVER={{{DRIVER}}};"
    f"SERVER={SERVER};"
    f"DATABASE={SOURCE_DB};"
    "Trusted_Connection=yes;"
    "TrustServerCertificate=yes;"
)

CONNECTION_STRING_Target = (
    f"DRIVER={{{DRIVER}}};"
    f"SERVER={SERVER};"
    f"DATABASE={TARGET_DB};"
    "Trusted_Connection=yes;"
    "TrustServerCertificate=yes;"
)
