"""
   CodeCraft PMS Backend Project

   파일명   : subject.py                                                          
   생성자   : 김창환                                                         
                                                                              
   생성일   : 2025/02/14                                             
   업데이트 : 2025/02/14                                      
                                                                              
   설명     : 교과목 관련 엔드포인트 정의
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import sys, os

sys.path.append(os.path.abspath('/data/Database Project'))
import subject_DB

router = APIRouter()