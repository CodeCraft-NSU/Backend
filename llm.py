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
from docx import Document
import sys, os, re

sys.path.append(os.path.abspath('/data/Database Project'))  # Database Project와 연동하기 위해 사용
import project_DB, output_DB

router = APIRouter()

"""
      LLM 통신 절차

      1. DB로부터 프로젝트의 기본 정보 및 온라인 산출물 정보를 받아온다.
      2. Storage Server로부터 MS Word (docx, doc, ...) 파일을 받아와 내용을 파싱한다.
      3. 위 두 정보를 가공한 뒤 ChatGPT에 정보를 전달한다.
      4. 필요에 따라 추가적으로 프롬프트를 전달한다.
      5. ChatGPT에게 받은 응답을 프론트엔드에 전달한다.
"""

# 프로젝트 종료 일까지 100일 이하로 남았다면 수능처럼 디데이 알려주는 기능 만들기?

class llm_payload(BaseModel):
   pid: int

def db_data_collect(pid):
   return project_DB.fetch_project_for_LLM(pid)

def output_data_collect(pid):
   data = output_DB.fetch_all_other_documents(pid)
   result = analysis_output(data)
   return result

def analysis_output(data):
   print(data)
   # 개쩌는 문서 파싱 기능 구현 #
   return result

def interact_gpt():
   # ChatGPT와 세션을 맺는 기능 구현
   return "Bye!"

@router.post("/llm/init")
async def api_llm_init(payload: llm_payload):
   db_data = db_data_collect(payload.pid)
   output_data = output_data_collect(payload.pid)
   return "Hi!"
