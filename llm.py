"""
   CodeCraft PMS Backend Project

   파일명   : llm.py                                                          
   생성자   : 김창환                                                         
                                                                              
   생성일   : 2024/11/26                                                  
   업데이트 : 2025/01/11                                
                                                                              
   설명     : llm 통신 관련 엔드포인트 정의
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from docx import Document
from openai import OpenAI
import sys, os, re, requests, json

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

"""
      GPT 프롬프트 설계

      CodeCraft PMS (이하 PMS)는 Project Management System으로서, 기존의 서비스로는 대학생이 제대로 사용하기 힘들었다는 것을 개선하기 위해 만든 서비스이다.

      너는 이 PMS를 사용하는 대학생들에게 도움을 주기 위해 사용될 것이다.
      모든 응답은 무조건 한국어로 답해주어야 하며, PMS와 관련되지 않은 질문은 모두 'PMS와 관련된 질문을 해주세요.'라고 응답한다.

      이 PMS는 코드보단 산출물 관리를 중점으로 진행하며, 다루게 될 산출물은 다음과 같다.
      SOW, WBS, ...

      이 중에서 PMS에서 자체적으로 작성 및 수정할 수 있는 산출물 (이하 온라인 산출물)은 다음과 같다: WBS, 개요서, 회의록, 테스트케이스, 요구사항 명세서, 보고서.
      온라인 산출물은 {db_data}에 포함되어 있으며, 이곳에 포함되지 않은 산출물은 {output_data}에 포함되어 있을 수도 있다.

      {output_data}에는 PMS에서 자체적으로 제공해주지 않는 산출물에 대한 정보가 들어있으며, ms word 형식으로 저장된 파일을 python을 통해 데이터를 가공해 데이터를 넘겨준 것이다.
      그렇기 때문에 ms word로 작성되지 않은 문서는 데이터로 가공이 불가능해 데이터에서 누락됐을 수 있다.
      데이터로 가공이 불가능한 문서의 경우 파일의 제목만 {output_data}에 첨부해 전달한다.
"""

# 프로젝트 종료 일까지 100일 이하로 남았다면 수능처럼 디데이 알려주는 기능 만들기?

class keypayload(BaseModel):
   pid: int
   api_key: str

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

def load_key(pid):
    try:
        with open('llm_key.json', 'r') as f: llm_key = json.load(f)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="llm_key.json file not found")
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="llm_key.json file is not valid JSON")
    for item in llm_key:
        if item["pid"] == pid: return item["api_key"]
    raise HTTPException(status_code=404, detail=f"Key with pid {pid} not found")

# 팀장만 등록 및 수정 가능하게 프론트에서 먼저 권한 확인 필요 #

@router.post("/llm/add_key")
async def api_add_key(payload: keypayload):
   try:
      with open('llm_key.json', 'r') as f: llm_key = json.load(f)
   except: llm_key = []
   add_data = {"pid": payload.pid, "api_key": payload.api_key}; llm_key.append(add_data)
   with open('llm_key.json', 'w') as f: json.dump(llm_key, f, indent=4)
   return {"RESULT_CODE": 200, "RESULT_MSG": f"API key for pid {payload.pid} added successfully"}

@router.post("/llm/edit_key")
async def api_edit_key(payload: keypayload):
    try: 
      with open('llm_key.json', 'r') as f: llm_key = json.load(f)
    except FileNotFoundError:
      raise HTTPException(status_code=404, detail="llm_key.json file not found")
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="llm_key.json file is not valid JSON")
    # pid 값을 기준으로 데이터 검색 및 업데이트
    updated = False
    for item in llm_key:
        if item["pid"] == payload.pid:
            item["api_key"] = payload.api_key
            updated = True
            break
    if not updated:
        raise HTTPException(status_code=404, detail=f"Key with pid {payload.pid} not found")
    # 변경된 데이터를 파일에 저장
    with open('llm_key.json', 'w') as f: json.dump(llm_key, f, indent=4)
    return {"RESULT_CODE": 200, "RESULT_MSG": f"API key for pid {payload.pid} updated successfully"}

###########################################################

@router.post("/llm/init")
async def api_llm_init(payload: llm_payload):
   db_data = db_data_collect(payload.pid)
   output_data = output_data_collect(payload.pid)
   return "Hi!"
