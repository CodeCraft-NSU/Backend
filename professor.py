"""
   CodeCraft PMS Backend Project

   파일명   : professor.py                                                          
   생성자   : 김창환                                                         
                                                                              
   생성일   : 2025/03/17
   업데이트 : 2025/03/17
                                                                              
   설명     : 교수 계정 관련 엔드포인트
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from logger import logger
import sys, os

sys.path.append(os.path.abspath('/data/Database Project'))  # Database Project와 연동하기 위해 사용
import project_DB
import account_DB