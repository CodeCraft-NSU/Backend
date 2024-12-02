"""
   CodeCraft PMS Backend Project

   파일명   : llm.py                                                          
   생성자   : 김창환                                                         
                                                                              
   생성일   : 2024/11/26                                                  
   업데이트 : 2024/11/26                                                       
                                                                              
   설명     : llm 통신 관련 엔드포인트 정의
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import sys, os

# sys.path.append(os.path.abspath('/data/Database Project'))  # Database Project와 연동하기 위해 사용
# import wbs_DB

router = APIRouter()