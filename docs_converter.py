"""
   CodeCraft PMS Backend Project

   파일명   : docs_converter.py                                                          
   생성자   : 김창환                                                         
                                                                              
   생성일   : 2024/11/26                                                      
   업데이트 : 2024/11/26                                                       
                                                                              
   설명     : DB로부터 정보를 받아와 문서화 해주는 기능 정의
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import sys, os

# sys.path.append(os.path.abspath('/data/Database Project'))  # Database Project와 연동하기 위해 사용
# import wbs_DB

router = APIRouter()

class ConverterPayload(BaseModel):
    pid: int
    univ_id: int
    doc_type: int
    doc_s_no: int

@router.post("/docs/convert")
async def docs_convert(payload: ConverterPayload):
    return {}