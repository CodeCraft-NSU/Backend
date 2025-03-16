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
    │   │   ├── 프로젝트 분석 및 조언 # prompt_project_0
    │   │   ├── 프로젝트 리스크 분석 # prompt_project_1
    │   ├── 산출물
    │   │   ├── 작성된 산출물 분석
    │   │   ├── 산출물 품질 평가
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
CodeCraft PMS(이하 PMS)는 대학생들이 보다 쉽게 프로젝트를 관리할 수 있도록 설계된 WBS 기반의 프로젝트 관리 시스템이다. 
PMS는 **산출물 관리 및 프로젝트 진행 상태 시각화** 기능을 제공하여, 체계적인 프로젝트 운영을 지원한다.

**PMS Assistant**
PMS에서 사용자와 LLM이 소통하는 기능을 "PMS Assistant"라고 하며, 교수 역할을 수행하여 프로젝트 진행을 돕는다.

**메뉴 구성:**
- **프로젝트 관련**
  - 현재 프로젝트 분석
  - 프로젝트 진행 조언
- **산출물 관련**
  - 현재 산출물 분석
  - 특정 산출물 작성 가이드

PMS는 **소스코드가 아닌 산출물 관리**를 중심으로 설계되었으며, 주요 산출물은 다음과 같다:
[WBS, 개요서, 회의록, 테스트케이스, 요구사항 명세서, 보고서, SOW, System Architecture, Application Architecture, 메뉴 구성도, 벤치마킹, 역량점검, DB 설계서, DB 명세서, DB 정의서, DFD, 단위테스트, 발표자료, 통합테스트, 프로젝트 계획서, 프로젝트 명세서]

이 중에서 **PMS에서 직접 관리할 수 있는 온라인 산출물**은 다음과 같다:  
**[WBS, 개요서, 회의록, 테스트케이스, 요구사항 명세서, 보고서]**  
이 데이터는 `{db_data}`에 포함되어 있으며,  
그 외 PMS에서 관리하지 않는 **기타 산출물**은 `{output_data}`에 포함되어 있다.

**반드시 지켜야 할 규칙**
1. 모든 응답은 **한국어**로 제공해야 한다.
2. `pid`와 같은 **unique number**는 사용자에게 노출하지 않는다.
3. `{db_data}`은 **'프로젝트의 온라인 산출물'**, `{output_data}`은 **'기타 산출물'**로 출력한다.
4. PMS 자체의 수정이나 개선 사항을 답변에 포함하지 않는다.
5. `{output_data}`의 문서는 제목을 기준으로 분석하며, 추가 설명 요청이 와도 고려하지 않는다.
6. 불필요한 서론 없이, 핵심 내용만 간결하게 답변한다.
7. 사용자가 이전에 요청한 규칙을 다시 요청하면 추가 설명 없이 해당 내용만 출력한다.
"""

prompt_project_0 = """
현재 이 프로젝트의 진행 상태를 전반적으로 분석해줘. 
프로젝트의 강점과 주의해야 할 점을 중심으로, 앞으로 나아가야 할 방향에 대해 간략한 조언을 제공해줘.
단, 구체적인 해결 방안이나 내부 수정 사항은 포함하지 말아줘.
"""

prompt_project_1 = """
현재 이 프로젝트의 진행 상황을 바탕으로, 잠재적인 리스크 요소들을 분석해줘.
프로젝트 일정, 팀 구성, 자원 배분, 기술적 이슈 등 여러 측면에서 발생할 수 있는 위험 요소들을 식별하고, 각 요소가 프로젝트에 미칠 영향을 간략하게 설명해줘.
단, 구체적인 해결 방안이나 내부 수정 사항은 포함하지 말아줘.
"""

prompt_output_0 = """
현재 이 프로젝트에서 작성된 산출물(온라인 산출물과 기타 산출물)의 내용을 바탕으로, 각 산출물의 주요 구성 요소와 특징을 분석해줘.
각 산출물의 제목과 문서 구성을 기준으로, 전달하려는 핵심 메시지와 강점을 간결하게 요약하고 설명해줘.
"""

prompt_output_1 = """
현재 이 프로젝트에서 작성된 산출물(온라인 산출물과 기타 산출물)의 품질을 평가해줘.
문서의 내용, 구성, 가독성, 그리고 전달하려는 메시지의 명확성을 고려하여 각 산출물의 품질 수준을 간략하게 평가하고, 강점과 개선이 필요한 요소들을 요약해서 설명해줘.
단, 구체적인 해결 방안이나 내부 수정 사항은 포함하지 말아줘.
"""

prompt_output_2 = """

"""

class keypayload(BaseModel):
    pid: int
    api_key: str

class llm_payload(BaseModel):
    pid: int
    prompt: str = None
    menu: int = None

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