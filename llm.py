"""
   CodeCraft PMS Backend Project

   파일명   : llm.py                                                          
   생성자   : 김창환                                                         
                                                                              
   생성일   : 2024/11/26                                                  
   업데이트 : 2024/12/03                                                
                                                                              
   설명     : llm 통신 관련 엔드포인트 정의
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import sys, os

sys.path.append(os.path.abspath('/data/Database Project'))  # Database Project와 연동하기 위해 사용
import project_DB

router = APIRouter()

class llm_payload(BaseModel):
   pid: int

@router.post("/llm/data")
async def llm_data_collect(payload: llm_payload):
   data = project_DB.fetch_project_for_LLM(payload.pid)
   return data

"""
GPT 프롬프트 작성 설계

작성 중...
"""