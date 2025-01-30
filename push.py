"""                                                          
   CodeCraft PMS Backend Project                             
                                                                              
   파일명   : push.py                                                          
   생성자   : 김창환                                
                                                                              
   생성일   : 2025/01/25                                                  
   업데이트 : 2025/01/25                                     
                                                                             
   설명     : Next.JS에 파일을 전송하는 함수 정의
"""

import logging
import requests
from fastapi import HTTPException
from urllib.parse import quote

def push_to_nextjs(file_path, file_name):
    try:
        try:
            logging.info(f"Sending file {file_name} to Next.js using Raw Binary")

            with open(file_path, "rb") as file:
                response = requests.post(
                    "http://192.168.50.84:90/api/file_receive",
                    data=file,
                    headers={
                        "Content-Type": "application/octet-stream",
                        "file-name": quote(file_name)
                    }
                )
            if response.status_code != 200:
                logging.error(f"Frontend server response error: {response.status_code} - {response.text}")
                raise HTTPException(status_code=500, detail="Failed to send file to frontend")

            logging.info(f"File {file_name} successfully transferred to frontend")
            return {"RESULT_CODE": 200, "RESULT_MSG": "File transferred successfully"}

        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to send file to frontend: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Request to frontend failed: {str(e)}")

    except Exception as e:
        logging.error(f"Unexpected error during file transfer: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")