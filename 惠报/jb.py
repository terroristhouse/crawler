import pyodbc

conn = pyodbc.connect(r'DRIVER={SQL Server};SERVER=localhost;DATABASE=HKNEWS;UID=sa;PWD=root')
cursor = conn.cursor()

cursor.execute("""
IF OBJECT_ID('HUIBAO', 'U') IS NOT NULL
    DROP TABLE HUIBAO
CREATE TABLE HUIBAO (
    url varchar(255),
    urlforpublish varchar(255),
    title varchar(255),
    source varchar(255),
    publishtime varchar(255)
)
""")
conn.commit()
cursor.close()
conn.close()











