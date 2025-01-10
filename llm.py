"""
   CodeCraft PMS Backend Project

   파일명   : llm.py                                                          
   생성자   : 김창환                                                         
                                                                              
   생성일   : 2024/11/26                                                  
   업데이트 : 2025/01/10                                               
                                                                              
   설명     : llm 통신 관련 엔드포인트 정의
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import sys, os

sys.path.append(os.path.abspath('/data/Database Project'))  # Database Project와 연동하기 위해 사용
import project_DB

router = APIRouter()

"""
      LLM 통신 절차

      1. DB로부터 프로젝트의 기본 정보 및 온라인 산출물 정보를 받아온다.
      2. Storage Server로부터 MS Word (docx, doc, ...) 파일을 받아와 내용을 파싱한다.
      3. 위 두 정보를 가공한 뒤 ChatGPT에 정보를 전달한다.
      4. 필요에 따라 추가적으로 프롬프트를 전달한다.
"""

class llm_payload(BaseModel):
   pid: int

def db_data_collect(pid):
   return {project_DB.fetch_project_for_LLM(payload.pid)}

def other_data_collect(pid):
   return {}

def analysis_msword():
   return {}

@router.post("/llm/init")
async def llm_data_collect(payload: llm_payload):
   return {}