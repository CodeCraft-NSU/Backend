import pymysql
from dotenv import load_dotenv
import os

load_dotenv()
password = os.getenv('DB_PASSWORD')

connection = pymysql.connect(
    host='192.168.50.84',
    user='root',
    password=password,
    charset='utf8mb4'
)

# try:
#     with connection.cursor() as cursor:
#         cursor.execute("SHOW DATABASES")
#         databases = cursor.fetchall()
#         print("Databases:")
#         for db in databases:
#             print(db[0])
# finally:
#     connection.close()
