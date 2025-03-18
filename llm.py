"""
   CodeCraft PMS Backend Project

   파일명   : llm.py                                                          
   생성자   : 김창환                                                         
                                                                              
   생성일   : 2024/11/26
   업데이트 : 2025/03/18
                                                                              
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
    │   │   ├── 작성된 산출물 분석 # prompt_output_0
    │   │   ├── 산출물 품질 평가 # prompt_output_1
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

온라인 산출물 데이터는 각 요소별로 가공되어 이어 붙여지며, 각 요소는 다음과 같이 구성된다:

- **프로젝트 정보:** 각 항목은 순서대로 아래 필드로 구성된다.
    - p_no: 프로젝트 번호 (사용하지 않음)
    - p_name: 프로젝트 제목
    - p_content: 프로젝트 설명
    - p_method: 프로젝트 개발 방식
    - p_memcount: 참여 인원 수
    - p_start: 프로젝트 시작일
    - p_end: 프로젝트 종료일
    - s.subj_name: 과목명  
  예시: [34772, "대학생을 위한 PMS 개발 프로젝트", "대학생이 사용 가능한 Project Management System을 개발하는 것을 목표로 합니다.", "2", 0, "2024-09-02", "2025-06-30", "[졸업작품][캡스톤]캡스톤디자인2"]
    - 단, p_no는 불필요한 정보이므로 활용하지 않는다.

- **업무:** 각 업무 항목은 순서대로 아래 필드로 구성된다.
    - w_name: 업무 이름
    - w_person: 업무 담당자
    - w_start: 업무 시작일
    - w_end: 업무 마감일
    - w_checked: 업무 완료 여부  
  예시: ["발표 준비", "김서진", "2025-03-17", "2025-03-17", 0]

- **WBS:** 각 WBS 항목은 순서대로 아래 필드로 구성된다.
    - group1: 대분류
    - group2: 중분류
    - group3: 소분류
    - work: 작업명
    - output_file: 산출물
    - manager: 담당자
    - ratio: 진척률
    - start_date: 시작일
    - end_date: 마감일  
  예시: ["계획", "프로젝트 아이디어/주제 탐색 및 계획", "", "프로젝트 수행 계획서 작성", "프로젝트 계획서", "이상훈, 김창환", 100.0, "2024-10-20", "2024-10-21"]
  
- **회의록:** 각 회의록 항목은 아래 필드로 구성된다.
    - doc_m_no: 회의록 번호 (사용하지 않음)
    - doc_m_title: 주요 안건 (회의록 제목)
    - doc_m_date: 회의 날짜
    - doc_m_loc: 회의 장소
    - doc_m_member: 회의 참여자
    - doc_m_manager: 회의 책임자
    - doc_m_content: 회의 내용
    - doc_m_result: 회의 결과
    - p_no: 프로젝트 번호 (사용하지 않음)  
  예시: [2, "캡스톤 디자인 프로젝트 기획", "2024-08-15", "재택", "김창환;20102056 , 이상훈;20102095, 김서진;20102048 , 이미르;20102093", "김서진", "프로젝트 주제 선별 및 방향성 계획", "팀원들의 역할 방향성 설정.\n\n개발 방향성 논의 -> 웹 방향으로 목표.\n\n초기 단계인 만큼 아직 미흡한 부분이 있어 17일 추가 회의 예정.\n-> 다음 회의 주제 방향성 추가 정리.", 34772]
    - 단, doc_m_no와 p_no는 불필요한 정보이므로 활용하지 않는다.

- **개요서:** 각 개요서 항목은 순서대로 아래 필드로 구성된다.
    - doc_s_no: 산출물 번호 (사용하지 않음)
    - doc_s_name: 프로젝트 제목
    - doc_s_overview: 프로젝트 개요
    - doc_s_goals: 프로젝트 목표
    - doc_s_range: 프로젝트 범위
    - doc_s_outcomes: 기대 성과
    - doc_s_team: 팀 구성 및 역할 분담
    - doc_s_stack: 기술 스택 및 도구
    - doc_s_start: 프로젝트 시작일
    - doc_s_end: 프로젝트 종료일
    - doc_s_date: 개요서 작성일
    - p_no: 프로젝트 번호 (사용하지 않음)  
  예시: [3, "대학생을 위한 웹 기반의 PMS 구축", "대학생들을 위한 PMS 개발로, 교수와 학생 모두가 프로젝트를 효율적으로 관리할 수 있도록 돕는다.", "프로젝트 관리 및 협업 지원", "프로젝트 범위 내 업무 및 산출물 관리", "프로젝트 성공을 위한 체계적 관리", "김창환, 김서진, 이미르, 이상훈", "HTML, CSS, JavaScript, React, Next.JS, AXIOS, Python, FastAPI, MySQL, PyMySQL", "2024-09-02", "2025-06-13", "2025-03-18", 34772]
    - 단, doc_s_no와 p_no는 불필요한 정보이므로 활용하지 않는다.

- **요구사항 명세서:** 각 요구사항 명세서 항목은 순서대로 아래 필드로 구성된다.
    - doc_r_no: 산출물 번호 (사용하지 않음)
    - doc_r_f_name: 기능 요구사항
    - doc_r_f_content: 기능 요구사항 설명
    - doc_r_f_priority: 기능 요구사항 우선순위
    - doc_r_nf_name: 비기능 요구사항
    - doc_r_nf_content: 비기능 요구사항 설명
    - doc_r_nf_priority: 비기능 요구사항 우선순위
    - doc_r_s_name: 시스템 요구사항
    - doc_r_s_content: 시스템 요구사항 설명
    - doc_r_date: 명세서 작성일  
  예시: ["로그인 기능", "사용자가 이메일과 비밀번호를 입력하여 로그인할 수 있다.", "높음", "보안", "비밀번호 암호화 적용", "중간", "시스템 성능", "동시 사용자 1000명 지원", "2024-08-20"]
    - 단, doc_r_no는 불필요한 정보이므로 활용하지 않는다.

- **테스트케이스:** 각 테스트케이스 항목은 순서대로 아래 필드로 구성된다.
    - DOC_T_NO: 테스트 번호 (사용하지 않음)
    - DOC_T_GROUP1: 테스트 분류
    - DOC_T_NAME: 테스트 항목 이름
    - DOC_T_START: 테스트 시작일
    - DOC_T_END: 테스트 종료일
    - DOC_T_PASS: 테스트 통과 여부
    - DOC_T_GROUP1NO: 테스트 분류 번호
    - P_NO: 프로젝트 번호 (사용하지 않음)  
  예시: [101, "기능 테스트", "로그인 기능 테스트", "2024-10-01", "2024-10-02", 1, 1, 34772]
    - 단, DOC_T_NO와 p_no는 불필요한 정보이므로 활용하지 않는다.

- **보고서:** 각 보고서 항목은 순서대로 아래 필드로 구성된다.
    - DOC_REP_NO: 산출물 번호 (사용하지 않음)
    - DOC_REP_NAME: 보고서 제목
    - DOC_REP_WRITER: 보고서 작성자
    - DOC_REP_DATE: 보고서 작성일
    - DOC_REP_PNAME: 프로젝트 제목
    - DOC_REP_MEMBER: 프로젝트 팀원
    - DOC_REP_PROFESSOR: 담당 교수
    - DOC_REP_RESEARCH: 문제 정의 및 연구 목표
    - DOC_REP_DESIGN: 설계 및 개발 과정
    - DOC_REP_ARCH: 시스템 아키텍처
    - DOC_REP_RESULT: 실험 및 결과
    - DOC_REP_CONCLUSION: 결론
    - P_NO: 프로젝트 번호 (사용하지 않음)  
  예시: ["보고서 제목 예시", "홍길동", "2024-11-30", "대학생을 위한 PMS 개발 프로젝트", "팀원1, 팀원2, 팀원3", "교수님", "문제 정의 및 목표 설명", "설계 및 개발 과정 설명", "시스템 아키텍처 설명", "실험 결과 설명", "결론 설명"]
    - 단, DOC_REP_NO와 p_no는 불필요한 정보이므로 활용하지 않는다.

그 외 PMS에서 관리하지 않는 **기타 산출물** 데이터도 별도로 이어 붙여진다.

최종 프롬프트는 이 prompt_init의 내용 뒤에,  
1. 온라인 산출물 데이터 (format_db_data를 통해 가공된 결과)  
2. 기타 산출물 데이터 (output_data_collect의 결과)  
3. 사용자가 요청한 프롬프트  
를 순서대로 이어붙여서 구성된다.
  
**반드시 지켜야 할 규칙**
1. 모든 응답은 **한국어**로 제공해야 한다.
2. `pid`와 같은 **unique number**는 사용자에게 노출하지 않는다.
3. 온라인 산출물 데이터는 각각 **'프로젝트 정보'**, **'업무'**, **'WBS'**, **'회의록'**, **'개요서'**, **'요구사항 명세서'**, **'테스트케이스'**, **'보고서'**로 구분되어 분석되어야 한다.
4. PMS 자체의 수정이나 개선 사항은 답변에 포함하지 않는다.
5. 기타 산출물 데이터는 제목을 기준으로 분석하며, 추가 설명 요청이 와도 고려하지 않는다.
6. 불필요한 서론 없이 핵심 내용만 간결하게 답변한다.
7. 사용자가 이전에 요청한 규칙을 다시 요청하면 추가 설명 없이 해당 내용만 출력한다.
8. 불필요하게 산출물의 리스트는 출력하지 않는다.
"""


PROMPTS = [
    """
    현재 이 프로젝트의 진행 상태를 전반적으로 분석해줘. 
    프로젝트의 강점과 주의해야 할 점을 중심으로, 앞으로 나아가야 할 방향에 대해 간략한 조언을 제공해줘.
    단, 구체적인 해결 방안이나 내부 수정 사항은 포함하지 말아줘.
    """, # prompt_project_0
    """
    현재 이 프로젝트의 진행 상황을 바탕으로, 잠재적인 리스크 요소들을 분석해줘.
    프로젝트 일정, 팀 구성, 자원 배분, 기술적 이슈 등 여러 측면에서 발생할 수 있는 위험 요소들을 식별하고, 각 요소가 프로젝트에 미칠 영향을 간략하게 설명해줘.
    단, 구체적인 해결 방안이나 내부 수정 사항은 포함하지 말아줘.
    """, # prompt_project_1
    """
    현재 이 프로젝트에서 작성된 산출물(온라인 산출물과 기타 산출물)의 내용을 바탕으로, 각 산출물의 주요 구성 요소와 특징을 분석해줘.
    각 산출물의 제목과 문서 구성을 기준으로, 전달하려는 핵심 메시지와 강점을 간결하게 요약하고 설명해줘.
    """, # prompt_output_0
    """
    현재 이 프로젝트의 온라인 산출물에 대한 품질 평가를 수행해줘.
    데이터는 {db_data}와 {output_data}로 구분되며, {db_data}의 구조는 다음과 같다:
    project: 프로젝트 정보, work_list: 업무, progress_list: 진척도 및 WBS 관련 데이터, meeting_list: 회의록, summary_list: 개요서, requirement_list: 요구사항 명세서, test_list: 테스트케이스, report_list: 보고서
    특히 progress_list 내에서 "WBS 작성" 또는 "WBS"와 관련된 항목은 반드시 'WBS' 산출물로 인식하여 평가에 포함해줘.
    {output_data}는 기타 산출물로 취급하며, 불필요한 산출물 리스트는 출력하지 말아줘.
    모든 응답은 한국어로 제공하고, 불필요한 서론 없이 핵심 내용만 간결하게 답변해줘.
    또한, 민감한 정보(예: pid)는 사용자에게 노출하지 말아줘.
    단, 구체적인 해결 방안이나 내부 수정 사항은 포함하지 말아줘.
    """ # prompt_output_1
]

class keypayload(BaseModel):
    pid: int
    api_key: str

class llm_payload(BaseModel):
    pid: int
    prompt: str = None
    menu: int = None

def db_data_collect(pid):
    data = project_DB.fetch_project_for_LLM(pid)
    if isinstance(data, str):
        try: data = json.loads(data)
        except json.JSONDecodeError as e:
            logger.error("DB 데이터 파싱 실패: " + str(e))
            raise HTTPException(status_code=500, detail="Invalid DB data format.")
    #logger.info("DB data: " + json.dumps(data, ensure_ascii=False))
    return data


def format_db_data(data: dict) -> str:
    parts = []
    if "project" in data:
        parts.append("프로젝트 정보: " + str(data["project"]))
    if "work_list" in data:
        parts.append("업무: " + str(data["work_list"]))
    if "progress_list" in data:
        parts.append("WBS: " + str(data["progress_list"]))
    if "meeting_list" in data:
        parts.append("회의록: " + str(data["meeting_list"]))
    if "summary_list" in data:
        parts.append("개요서: " + str(data["summary_list"]))
    if "requirement_list" in data:
        parts.append("요구사항 명세서: " + str(data["requirement_list"]))
    if "test_list" in data:
        parts.append("테스트케이스: " + str(data["test_list"]))
    if "report_list" in data:
        parts.append("보고서: " + str(data["report_list"]))
    return "\n".join(parts)

def output_data_collect(pid):
   data = str(output_DB.fetch_all_other_documents(pid))
   #logger.info(f"Output data: " + data)
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
    db_raw_data = db_data_collect(pid)
    formatted_db_data = format_db_data(db_raw_data)
    output_data = output_data_collect(pid)
    data = f"[프로젝트의 온라인 산출물]\n{formatted_db_data}\n\n[기타 산출물]\n{output_data}"
    return data

@router.post("/llm/interact")
async def api_interact_gpt(payload: llm_payload):
    try:
        try: 
            key = load_key(payload.pid)  # Gemini key 로드
        except Exception as e:
            logger.debug(f"LLM process error while loading key for PID {payload.pid}: {str(e)}")
            raise HTTPException(status_code=500, detail="Key exception occurred.")
        genai.configure(api_key=key)
        model = genai.GenerativeModel("gemini-2.0-flash")  # Gemini 모델 선언
        # menu 값이 올바른 범위 내에 있는지 확인
        if 0 <= payload.menu < len(PROMPTS):
            selected_prompt = PROMPTS[payload.menu]
        else:
            logger.debug(f"Invalid menu value received: {payload.menu}")
            raise HTTPException(status_code=400, detail="Invalid menu value.")
        # 최종 프롬프트 구성
        prompt = prompt_init + "\n\n" + llm_init(payload.pid) + selected_prompt
        response = model.generate_content(prompt)
        logger.info(f"LLM response for project {payload.pid}, menuid {payload.menu}: {response.text}")
        return response.text
    except Exception as e:
        logger.debug(f"Unhandled Error occurred: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unhandled Error occurred while LLM process: {str(e)}")