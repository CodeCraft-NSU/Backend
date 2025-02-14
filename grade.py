"""                                                          
   CodeCraft PMS Backend Project                             
                                                                              
   파일명   : grade.py                                                          
   생성자   : 김창환                                
                                                                              
   생성일   : 2024/11/24                                                      
   업데이트 : 2025/01/30                                            
                                                                             
   설명     : 프로젝트를 평가와 관련 된 엔드포인트 정의
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import sys, os

sys.path.append(os.path.abspath('/data/Database Project'))  # Database Project와 연동하기 위해 사용
import grade_DB

router = APIRouter()

