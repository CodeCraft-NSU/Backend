"""                                                          
   CodeCraft PMS Backend Project                             
                                                                              
   파일명   : permission.py                                                          
   생성자   : 김창환                                
                                                                              
   생성일   : 2025/01/15                                                   
   업데이트 : 2025/01/15                                            
                                                                             
   설명     : 계정의 프로젝트 접근 권한을 조회하는 엔드포인트 정의
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import sys, os, requests

sys.path.append(os.path.abspath('/data/Database Project'))  # Database Project와 연동하기 위해 사용
import permission_DB

router = APIRouter()