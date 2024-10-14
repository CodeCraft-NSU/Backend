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
