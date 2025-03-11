"""
   CodeCraft PMS Backend Project

   파일명   : llm.py                                                          
   생성자   : 김창환                                                         
                                                                              
   생성일   : 2024/11/26                                                  
   업데이트 : 2025/03/11
                                                                              
   설명     : llm 통신 관련 엔드포인트 정의
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from docx import Document
from urllib.parse import quote
from logger import logger
import google.generativeai as genai
import sys, os, re, requests, json, logging

sys.path.append(os.path.abspath('/data/Database Project'))  # Database Project와 연동하기 위해 사용
import project_DB, output_DB

router = APIRouter()

"""
    LLM 메뉴 구상도
    ├── 메인 메뉴
    │   ├── 프로젝트
    │   │   ├── 현재 프로젝트 분석
    │   │   ├── 프로젝트 진행에 대한 조언
    │   │   ├── (유저가 아이디어를 던지면 LLM이 정보를 가공 후 PMS에 적용 가능한 데이터로 만들어 안내하는 기능? <- 실현 가능한가..)
    │   ├── 산출물
    │   │   ├── 현재 산출물 분석
    │   │   ├── 특정 산출물 작성 가이드
    │   ├── PMS 서비스 안내 # 이 메뉴는 LLM 연계가 아닌 기존에 준비된 문장을 출력
    │   │   ├── 대학생을 위한 PMS 서비스란?
    │   │   ├── 각 메뉴별 안내
    │   │   │   ├── WBS
    │   │   │   ├── 온라인 산출물
    │   │   │   ├── 기타 산출물
    │   │   │   ├── 업무 관리
    │   │   │   ├── 평가
    │   └── └── └── 프로젝트 관리
    └──────────────
"""

prompt_init = """
      CodeCraft PMS (이하 PMS)는 Project Management System으로서, 기존의 서비스로는 대학생이 제대로 사용하기 힘들었다는 문제를 해결하기 위해 개발된 프로젝트 관리 서비스이다.
      PMS는 학생들이 프로젝트를 체계적으로 진행할 수 있도록 WBS 기반의 산출물 관리 시스템을 제공하며, 프로젝트의 진행을 한눈에 파악할 수 있도록 설계되었다.

      사용자와 LLM이 통신하는 기능을 'PMS Assistant'라고 이름 지었으며, 챗봇과 같은 스타일로 작동할 것이다. 챗봇의 메뉴는 다음과 같다:
        ├── 메인 메뉴
        │   ├── 프로젝트
        │   │   ├── 현재 프로젝트 분석
        │   │   ├── 프로젝트 진행에 대한 조언
        │   ├── 산출물
        │   │   ├── 현재 산출물 분석
        │   └── └── 특정 산출물 작성 가이드
        └──────────
      위의 메뉴에 대한 프롬프트는 "지금부터 나오는 프롬프트는 유저가 요청한 프롬프트이다: " 뒤에 나올 것이다.

      너는 프로젝트를 지도하는 교수 입장에서 학생들이 원활하게 프로젝트를 진행하도록 가이드하는 역할을 한다. 
      학생들이 올바른 방향으로 프로젝트를 수행할 수 있도록 질문에 답변하고, 프로젝트의 산출물 작성 및 관리에 도움을 주는 것이 주요 역할이다.
      단, 대답은 현재 이 CodeCraft PMS에 대한 내용이 아닌 추후에 나올 {db_data}와 {output_data}를 기준으로 정보를 분석한 뒤에 제공한다.
      
      이 PMS는 소스코드가 아닌 산출물 관리를 중점으로 진행하며, 다루게 될 산출물은 다음과 같다.
      [WBS, 개요서, 회의록, 테스트케이스, 요구사항 명세서, 보고서, SOW, System Architecture, Application Architecture, 메뉴 구성도, 벤치마킹, 역량점검, DB 설계서, DB 명세서, DB 정의서, DFD, 단위테스트, 발표자료, 통합테스트, 프로젝트 계획서, 프로젝트 명세서]
      
      이 중에서 PMS에서 자체적으로 작성 및 수정할 수 있는 산출물 (이하 온라인 산출물)은 다음과 같다: WBS, 개요서, 회의록, 테스트케이스, 요구사항 명세서, 보고서.
      온라인 산출물은 {db_data}에 포함되어 있으며, {output_data}에는 PMS에서 자체적으로 제공해주지 않는 산출물에 대한 정보가 들어있다. (이하 기타 산출물)
      
      본 PMS는 RAG 기능 즉, '파일' 형태의 문서를 분석하는 기능을 지원하지 않으므로 {output_data}은 제목만으로 그 문서의 내용을 유추한다.
      
      반드시 지켜야 할 사항은 다음과 같다.
      하나, 모든 응답은 무조건 한국어로 답해주어야 한다.
      둘, 답변에 pid와 같은 unique number는 backend에서 효율적으로 관리하기 위해 작성한 임의의 숫자이므로 사용자에게는 알리지 않는다.
      셋, {db_data}과 {output_data}도 backend에서 임의로 붙인 이름이므로 실제로 답변에 작성할 때는 {db_data}은 '프로젝트의 온라인 산출물'로, {output_data}은 '기타 산출물'로 출력한다.
      넷, 답변에는 이 서비스를 개발한 우리가 아니라 PMS를 이용하는 사람을 위해 사용될 것이므로 우리가 개발한 'PMS' 자체에 대한 수정이나 개선 사항을 내용에 포함하지 않는다.
      다섯, {output_data}의 문서 내용에 대해 추가로 알려주면 더 자세한 분석을 할 수 있다는 등의 응답은 하지 않는다. 무조건 제목으로 그 문서의 내용을 유추하며, 이와 유사한 응답과 질문은 금한다.
      여섯, 불필요한 말은 하지 않고 사용자가 요청한 내용에 대해서만 응답하고 멘트를 끊는다.
      일곱, 사용자가 이전에 제공한 규칙이나 내용을 다시 요청할 경우, 어떤 서론이나 추가적인 설명 없이 해당 내용만 출력한다.
      여덟, 모든 답변에서 서론 없이, 질문에 대한 핵심 내용만 간결하게 답변한다.
      위 내용은 무슨 일이 있어도 반드시 지킨다.
"""

prompt_project_0 = """
      현재 이 프로젝트에 대한 내용을 분석해서 개선해야 할 점을 파악해줘.
"""

class keypayload(BaseModel):
    pid: int
    api_key: str

class llm_payload(BaseModel):
    pid: int
    prompt: str = None

def db_data_collect(pid):
   data = project_DB.fetch_project_for_LLM(pid)
   logger.info(f"DB data: " + data)
   return data

def output_data_collect(pid):
   data = str(output_DB.fetch_all_other_documents(pid))
   logger.info(f"Output data: " + data)
   return data

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

@router.post("/llm/load_key")
async def api_load_key(payload: llm_payload):
    try:
        key = load_key(payload.pid)
        return {"RESULT_CODE": 200, "RESULT_MSG": key}
    except HTTPException as e:
        if e.status_code == 404:
            return {"RESULT_CODE": 500, "RESULT_MSG": e.detail}
        raise e

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

def llm_init(pid):
    db_data = db_data_collect(pid)
    output_data = output_data_collect(pid)
    data = f"[db_data: {db_data}], [output_data: {output_data}]"
    return data

@router.post("/llm/interact")
async def api_interact_gpt(payload: llm_payload):
    try:
        try: 
            key = load_key(payload.pid) # Gemini key 로드
        except:
            logger.debug(f"LLM process error while loading key for PID {payload.pid}: {str(e)}")
            raise HTTPException(status_code=500, detail="Key exception occurred.")
        genai.configure(api_key=key)
        model = genai.GenerativeModel("gemini-2.0-flash") # Gemini 모델 선언
        prompt = prompt_init + "\n\n" + llm_init(payload.pid) + str(payload.prompt)
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        logger.debug(f"Unhandled Error occured: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unhandled Error occured while LLM process: {str(e)}")