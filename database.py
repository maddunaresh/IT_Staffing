from sqlalchemy import create_engine
from sqlalchemy.engine import URL

connection_string = (
    "DRIVER={ODBC Driver 18 for SQL Server};"
    r"SERVER=NARESH\SQLSERVERLAB;"
    "DATABASE=USITStaffingDB;"
    "Trusted_Connection=yes;"
    "Encrypt=yes;"
    "TrustServerCertificate=yes;"
)

database_url = URL.create(
    "mssql+pyodbc",
    query={"odbc_connect": connection_string},
)

engine = create_engine(database_url, pool_pre_ping=True)