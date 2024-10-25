"""                                                          
   CodeCraft PMS Project                             
                                                                              
   파일명   : mysql_connection.py                                                          
   생성자   : 김창환                                
                                                                              
   생성일   : 2024/10/14
   업데이트 : 2024/10/20
                                                                             
   설명     : API와 DB를 연결하는 기능 정의
"""

import pymysql
from dotenv import load_dotenv
import os

def db_connect():
    load_dotenv()
    password = os.getenv('DB_PASSWORD')

    connection = pymysql.connect(
        host='192.168.50.84',
        user='root',
        password=password,
        charset='utf8mb4'
    )

# try: # DB에 접속해 테이블 리스트 출력
#     with connection.cursor() as cursor:
#         cursor.execute("SHOW DATABASES")
#         databases = cursor.fetchall()
#         print("Databases:")
#         for db in databases:
#             print(db[0])
# finally:
#     connection.close()
