"""                                                          
   CodeCraft PMS Backend Project                             
                                                                              
   파일명   : ccp.py                                                          
   생성자   : 김창환                                
                                                                              
   생성일   : 2025/01/10                                                      
   업데이트 : 2025/01/10                                              
                                                                             
   설명     : 프로젝트 Import/Export API 엔드포인트 정의
"""

from fastapi import APIRouter, HTTPException, File, UploadFile
from pydantic import BaseModel
import os

router = APIRouter()

sys.path.append(os.path.abspath('/data/Database Project'))  # Database Project와 연동하기 위해 사용
import csv_DB

class ccp_payload(BaseModel):
    pid: int = None
    s_no: int = None

router.post("/ccp/import")
async def api_project_import(payload: ccp_payload):
    """프로젝트 불러오기"""
    return {}

router.post("/ccp/export")
async def api_project_import(payload: ccp_payload):
    """프로젝트 추출 기능"""
    return {}