"""
   CodeCraft PMS Backend Project

   파일명   : llm.py                                                          
   생성자   : 김창환                                                         
                                                                              
   생성일   : 2024/11/26                                                  
   업데이트 : 2025/01/30                
                                                                              
   설명     : llm 통신 관련 엔드포인트 정의
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from docx import Document
from urllib.parse import quote
import google.generativeai as genai
import sys, os, re, requests, json, logging

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

prompt_init = """
      CodeCraft PMS (이하 PMS)는 Project Management System으로서, 기존의 서비스로는 대학생이 제대로 사용하기 힘들었다는 것을 개선하기 위해 만든 서비스이다.

      너는 이 PMS를 사용하는 대학생들에게 프로젝트를 진행하는 데 도움을 주기 위해 사용될 것이다.
      모든 응답은 무조건 한국어로 답해주어야 한다.

      이 PMS는 코드보단 산출물 관리를 중점으로 진행하며, 다루게 될 산출물은 다음과 같다.
      WBS, 개요서, 회의록, 테스트케이스, 요구사항 명세서, 보고서, SOW, System Architecture, Application Architecture, 메뉴 구성도, 벤치마킹, 역량점검, DB 설계서, DB 명세서, DB 정의서, DFD, 단위테스트, 발표자료, 통합테스트, 프로젝트 계획서, 프로젝트 명세서

      이 중에서 PMS에서 자체적으로 작성 및 수정할 수 있는 산출물 (이하 온라인 산출물)은 다음과 같다: WBS, 개요서, 회의록, 테스트케이스, 요구사항 명세서, 보고서.
      온라인 산출물은 {db_data}에 포함되어 있으며, 이곳에 포함되지 않은 산출물은 {output_data}에 포함되어 있을 수도 있다.

      {output_data}에는 PMS에서 자체적으로 제공해주지 않는 산출물에 대한 정보가 들어있으며, docx로 저장된 파일을 python을 통해 데이터를 가공해 데이터를 넘겨준 것이다.
      그렇기 때문에 ms word로 작성되지 않은 문서는 데이터로 가공이 불가능해 데이터에서 누락됐을 수 있다.
      데이터로 가공이 불가능한 문서의 경우 파일의 제목만 {output_data}에 첨부해 전달한다.
      다만 현재 이 기능은 구현되지 않았으므로 {output_data}에 대한 내용은 무시하고, 온라인 산출물에 대한 내용만 생각한다.

      참고로, 답변에 pid와 같은 unique number는 backend에서 효율적으로 관리하기 위해 작성한 임의의 숫자이므로 실제 사용자는 알 필요가 없다.
      그렇기 때문에 내용에 이와 관련된 내용은 포함하지 않도록 한다.
      또한 {db_data}와 {output_data}도 backend에서 임의로 붙인 이름이므로 실제로 답변에 작성할 때는 {db_data}는 프로젝트/온라인 산출물 데이터로, {output_data}는 기타 산출물 데이터로 출력한다.
      답변에는 이 서비스를 개발한 우리가 아니라 PMS를 이용하는 사람을 위해 사용될 것이므로 우리가 개발한 'PMS' 자체에 대한 수정이나 개선 사항을 내용에 포함하지는 않도록 한다.
"""

# 프로젝트 종료 일까지 100일 이하로 남았다면 수능처럼 디데이 알려주는 기능 만들기?

class keypayload(BaseModel):
    pid: int
    api_key: str

class llm_payload(BaseModel):
    pid: int
    prompt: str = None

def db_data_collect(pid):
   return project_DB.fetch_project_for_LLM(pid)

def output_data_collect(pid):
   data = output_DB.fetch_all_other_documents(pid)
   result = analysis_output(data)
   return result

def analysis_output(data):
#    print(data)
   # 개쩌는 문서 파싱 기능 구현 #
   result = "output data는 아직 미구현 기능입니다."
   return result

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

def save_llm_data(pid, contents):
    path = "gpt/" + str(pid) + ".txt"
    with open(path, 'w') as f:
        f.write(contents)

@router.post("/llm/reconnect")
async def api_reconnect_gpt(payload: llm_payload):
    # PMS의 세션을 복원 시 GPT 통신 기록을 프론트에 전달 #
    try:
        logging.info(f"Sending gpt chat file to Next.js using Raw Binary")
        file_name = str(payload.pid) + ".txt"
        llm_file_path = "gpt/" + file_name
        with open(llm_file_path, "rb") as file:
            response = requests.post(
                "http://192.168.50.84:90/api/file_receive",
                data=file,
                headers={
                    "Content-Type": "application/octet-stream",
                    "file-name": quote(file_name)
                }
            )
        if response.status_code != 200:
            logging.error(f"Frontend server response error: {response.status_code} - {response.text}")
            raise HTTPException(status_code=500, detail="Failed to send file to frontend")

        logging.info(f"File {file_name} successfully transferred to frontend")
        return {"RESULT_CODE": 200, "RESULT_MSG": "File transferred successfully"}

    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to send file to frontend: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Request to frontend failed: {str(e)}")

def create_gpt_txt(pid):
    contents = prompt_init + "\n\n" + llm_init(pid)
    save_llm_data(pid, contents)

@router.post("/llm/interact")
async def api_interact_gpt(payload: llm_payload):
    # ChatGPT와 세션을 맺는 기능 구현 #

    gpt_chat_path = f"gpt/{payload.pid}.txt"
    if not os.path.isfile(gpt_chat_path): # 이전 프롬프트 기록이 없다면
        create_gpt_txt(payload.pid) # 프롬프트 기록 생성

    key = load_key(payload.pid) # Gemini key 로드
    genai.configure(api_key=key)
    model = genai.GenerativeModel("gemini-1.5-flash") # Gemini 모델 선언

    try:
        with open(gpt_chat_path, "r", encoding="utf-8") as file:
            previous_prompts = file.read() # 이전 프롬프트 기록 불러오기
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read {gpt_file_path}: {e}")

    new_prompt = f"{previous_prompts}\n\n{payload.prompt}" # 이전 프롬프트 + 신규 프롬프트
    response = model.generate_content(new_prompt) # 프롬프트 전송

    save_llm_data(payload.pid, response.text)
    """
    프롬프트 저장 단계의 개선이 필요함
    제대로 활용하려면 프롬프트와 응답을 모두 저장해야 하는데, 현재는 초기 프롬프트를 제외하면 응답만 저장하게 되어있음
    txt가 아니라 json을 이용할지, 아니면 두 파일을 분리한 후 하나씩 불러오게 할지..
    """
    return response.text