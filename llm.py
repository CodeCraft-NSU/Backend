"""
   CodeCraft PMS Backend Project

   파일명   : llm.py                                                          
   생성자   : 김창환                                                         
                                                                              
   생성일   : 2024/11/26
   업데이트 : 2025/04/27
                                                                              
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
    │   │   ├── 프로젝트 초기 기획 추천 # prompt_project_2
    │   ├── 산출물
    │   │   ├── 작성된 산출물 분석 # prompt_output_0
    │   │   ├── 산출물 품질 평가 # prompt_output_1
    │   ├── PMS 서비스 안내 # 이 메뉴는 LLM 연계가 아닌 기존에 준비된 문장을 출력
    │   │   ├── 대학생을 위한 PMS 서비스란? # manual_pms
    │   │   ├── 각 메뉴별 안내
    │   │   │   ├── WBS # manual_menu_0
    │   │   │   ├── 온라인 산출물 # manual_menu_1
    │   │   │   ├── 기타 산출물 # manual_menu_2
    │   │   │   ├── 업무 관리 # manual_menu_3
    │   │   │   ├── 평가 # manual_menu_4
    │   └── └── └── 프로젝트 관리 # manual_menu_5
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
  - 프로젝트 초기 기획 추천
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
    - p_method: 프로젝트 개발 방식, 각 번호가 의미하는 바는 다음과 같다: [0:폭포수, 1:애자일, 2:기타] 만약 p_method가 2라면 p_content에 개발 방식이 정의되어 있을 가능성이 있다. 만약 정의되어 있다면 2라는 이유로 문제를 삼지 않는다.
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
    현재 이 프로젝트는 주제만 선정된 초기 단계야.
    프로젝트 설명과 개발 방식을 바탕으로 다음 내용을 중심으로 조언해줘:

    1. p_method나 p_content에 정의된 프로젝트의 개발 방식 (애자일, 프로토타입 등)을 기반으로 주제에 맞는 WBS 내용을 구체적인 예시로 제시해줘.
    2. 앞으로 어떤 온라인 산출물을 어떤 순서와 방식으로 작성하면 좋을지 제안해주고, 각 산출물엔 실제로 어떤 내용이 들어가면 좋을지 구체적인 예시를 제시해줘.
    3. 현재 설정된 팀원의 인원수에 따라 효율적인 역할 분배 방법을 알려줘.
    4. 우리의 PMS를 어떤 방향으로 활용하면 프로젝트를 체계적으로 관리할 수 있을지 간단히 안내해줘.

    단, 아직 작성된 데이터가 거의 없다는 점을 고려해서, 구체적인 작업 지시보다는  
    생각을 정리하고 방향성을 잡을 수 있도록 간결하게 도와줘.
    """, # prompt_project_2
    """
    현재 이 프로젝트에서 작성된 산출물(온라인 산출물과 기타 산출물)의 내용을 바탕으로, 각 산출물의 주요 구성 요소와 특징을 분석해줘.
    각 산출물의 제목과 문서 구성을 기준으로, 전달하려는 핵심 메시지와 강점을 간결하게 요약하고 설명해줘.
    """, # prompt_output_0
    """
    현재 이 프로젝트의 온라인 산출물에 대한 품질 평가를 수행해줘.
    단, 불필요하게 산출물 리스트는 출력하지 말아주고, 구체적인 해결 방안이나 내부 수정 사항은 포함하지 말아줘.
    """ # prompt_output_1
]

manual_pms = """
대학생을 위한 Project Management System(PMS)은
"기존 상용 PMS의 복잡한 기능을 대학생 눈높이에 맞춰 간소화하자"는 목표로, 2024년부터 2025년까지 1년간 남서울대학교 캡스톤 디자인 프로젝트로 개발되었습니다.

기존 PMS에 포함된 CI/CD 등 대학생 수준에서 불필요한 기능은 제거하고, 프로젝트 규모도 축소하여, 산출물 중심의 프로젝트 진행에 집중할 수 있도록 설계되었습니다.

이 PMS를 통해 대학생들은 보다 쉽고 효율적으로 프로젝트를 계획하고 관리할 수 있습니다.
"""

manual_menu_0 = """
WBS (Work Breakdown Structure)
메뉴 위치: 프로젝트 관리 > WBS 관리

[기능 개요]  
WBS는 프로젝트를 단계별로 세분화하여 구조적으로 정리할 수 있는 기능입니다.  
대학생 팀 프로젝트에서는 역할 분담, 일정 관리, 산출물 추적 등을 보다 명확하게 할 수 있도록 도와줍니다.  
PMS에서는 ‘애자일’, ‘프로토타입’, ‘기타’와 같은 다양한 프로젝트 관리 방법론에 따라 WBS를 유연하게 작성할 수 있습니다.

[주요 화면 구성 및 입력 항목 설명]  
- 대분류 / 중분류 / 소분류 / 액티비티: 작업을 단계적으로 분류할 수 있는 입력칸입니다. 예) 계획 > 프로젝트 아이디어 > 세부활동  
- 작업명: 각 작업의 제목을 입력합니다. 예) 프로젝트 수행 계획  
- 산출물: 해당 작업으로부터 생성되는 결과물을 입력합니다. 예) 프로젝트 계획서  
- 담당자: 해당 작업의 수행자 이름을 입력합니다. 여러 명 입력 가능  
- 비고: 추가적인 설명이나 참고 내용을 입력합니다.  
- 진척률: 해당 작업의 진행 정도를 숫자(%)로 입력합니다. 0~100까지 입력 가능  
- 시작일 / 마감일: 각 작업의 시작과 종료 날짜를 설정합니다.  
- 위/아래 버튼: 작성된 작업의 순서를 조정할 수 있습니다.  
- 삭제 버튼: 해당 행을 삭제합니다.
- 행 추가: 작업을 한 줄 추가합니다.  
- 저장하기: 현재 작성된 WBS 내용을 저장합니다.  
- 초기화: 모든 작업 내용을 초기 상태로 되돌립니다.

[프로젝트 관리 방법론에 따른 WBS 작성 예시]

PMS에서는 프로젝트를 어떤 방식으로 진행할지 선택할 수 있도록, ‘애자일’, ‘폭포수’, ‘기타’ 세 가지 개발 방법론을 지원합니다.  
각 방법론은 작업을 어떤 순서와 구조로 나눌지(WBS 구성)에 영향을 줍니다.  
아래는 각 방법론에 맞춰 WBS를 어떻게 작성하면 되는지를 쉽게 설명한 내용입니다.

1. 애자일 방식  
‘애자일(Agile)’은 프로젝트를 짧은 단위로 나누어 반복적으로 작업하고, 그때그때 피드백을 받아 개선해 나가는 방식입니다.  
이러한 단위를 ‘스프린트(Sprint)’라고 부르며, 보통 1~2주에 한 번씩 새로운 작업을 계획하고 수행합니다.  
WBS는 각 스프린트를 기준으로 나누어 작성하며, 유동적으로 작업 순서를 조정하고, 반복되는 구조로 구성되는 경우가 많습니다.

예시)  
- 1차 스프린트  
  → 기획 회의  
  → 기본 기능 구현  
- 2차 스프린트  
  → 피드백 반영  
  → 기능 개선 및 테스트

이 방식은 **짧은 주기로 작업과 점검을 반복**하기 때문에, 변화에 유연하게 대응하고 팀원 간 협업을 활성화할 수 있습니다.

2. 폭포수 방식  
‘폭포수(Waterfall)’는 프로젝트를 단계별로 나누고, 한 단계가 끝나야 다음 단계로 넘어가는 전통적인 개발 방식입니다.  
WBS는 처음부터 끝까지 순차적으로 구성되며, 각 단계의 작업이 명확히 정의되어 있습니다.  
이 방식은 계획과 일정이 확실한 경우, 그리고 작업 흐름이 한 번에 정해진 경우에 적합합니다.

예시)  
→ 요구사항 분석  
→ 설계  
→ 개발  
→ 테스트  
→ 최종 제출

이 방식은 **예측 가능한 일정 관리**에 유리하지만, 중간에 변경 사항이 생기면 반영이 어렵다는 단점이 있습니다.

3. 기타 방식  
‘기타’는 PMS에서 직접적으로 구조를 제공하지 않는 방식으로 프로젝트를 진행하는 경우에 선택합니다.  
예를 들어, 프로토타입(Prototype) 방식처럼 시제품을 먼저 만든 후, 사용자의 피드백을 받아 여러 차례 수정하는 반복 중심의 방식이 이에 해당합니다.  

PMS에서는 프로토타입 방식처럼 비정형적인 흐름을 직접적으로 지원하지 않기 때문에, WBS를 사용자가 자유롭게 구성해야 합니다.

예시)  
→ 아이디어 스케치  
→ 1차 시제품 제작  
→ 사용자 피드백 수집  
→ 2차 시제품 개선  
→ 최종 시제품 제작 및 보고

이 방식은 직관적으로 먼저 만들어 보고, 그 후에 수정·보완을 반복하는 프로젝트에 적합하며, 디자인이나 창작 중심의 프로젝트에서 많이 사용됩니다.

---

정리하자면,  
- 애자일은 "짧은 기간 단위로 작업을 나누어 반복하며 개선하는 방식"입니다.  
- 폭포수는 "단계별로 순차적으로 진행하는 방식"입니다.  
- 기타는 "PMS가 직접 지원하지 않는 방식(예: 프로토타입)으로 자유롭게 구성하는 방식"입니다.

각 팀은 자신들의 프로젝트 성격에 맞는 방법론을 선택하여 WBS를 작성하면 됩니다.
"""

manual_menu_1 = """
온라인 산출물  
메뉴 위치: 산출물 작성

[기능 개요]  
‘온라인 산출물’은 프로젝트 진행 과정에서 필요한 각종 문서를 PMS 안에서 직접 작성하고 저장할 수 있는 기능입니다.  
문서는 Word(docx) 형식으로 출력 가능하며 (테스트 케이스 제외), 저장된 문서는 언제든지 다시 불러와 수정할 수 있습니다.

[지원되는 산출물 목록]
아래와 같은 항목을 지원하며, 각 산출물은 정해진 양식에 따라 입력하게 됩니다.

1. 개요서  
   - 프로젝트의 전체 개요와 목표, 기술 스택, 일정, 팀 구성 등을 작성합니다.  
   - 주요 항목: 제목, 시작일, 종료일, 팀 구성 및 역할 분담, 목표, 범위, 기술 스택, 기대 성과 등

2. 회의록  
   - 회의 일시, 안건, 참석자, 회의 내용 및 결정 사항 등을 기록합니다.  
   - 주요 항목: 안건, 날짜, 책임자, 장소, 참석자 정보, 회의 내용, 회의 결과 등

3. 테스트 케이스
   - 서비스나 기능을 테스트한 결과를 기록합니다.  
   - 주요 항목: 테스트 시작일/종료일, 테스트 항목명, 통과 여부 등

4. 요구사항  
   - 시스템과 기능에 대한 요구사항을 작성합니다.  
   - 주요 항목: 시스템 요구사항, 기능 요구사항, 비기능 요구사항 및 설명과 우선순위

5. 보고서  
   - 프로젝트의 전반적인 결과를 정리한 문서입니다.  
   - 주요 항목: 문제 정의, 설계 및 개발 과정, 시스템 구조, 실험 및 결과, 결론 등

[주요 기능]  
- 각 항목은 클릭 시 입력 폼이 열리며, 작성 후 저장할 수 있습니다.  
- ‘저장’ 버튼을 누르면 입력한 내용이 자동으로 보관되며, ‘다운로드’ 버튼을 통해 docx 문서로 저장할 수 있습니다.  
- 저장된 문서는 이후에도 수정이 가능합니다.

[사용 팁]  
- 산출물 작성을 미루지 않고, 단계별로 정리해두면 프로젝트 후반에 보고서를 작성할 때 큰 도움이 됩니다.  
- 회의록과 요구사항 문서는 팀원 간의 합의 내용을 남기는 데 효과적입니다.  
- 각 문서는 Word 형식으로 제출이 가능하므로, 학교나 교수님께 보고할 때도 그대로 활용할 수 있습니다.
"""

manual_menu_2 = """
기타 산출물  
메뉴 경로: 산출물 작성 > 기타

[기능 개요]  
‘기타 산출물’은 PMS에서 공식적으로 지원하지 않는 형식의 산출물을 업로드할 수 있는 공간입니다.  
주로 문서 외 파일이나 자유 형식 자료들을 첨부하고 보관하는 데 사용됩니다.
기타 산출물로 활용할 수 있는 문서는 산출물 관리 -> 자료실에 있습니다.

[사용 목적 및 예시]  
다음과 같은 산출물 또는 파일들을 업로드할 수 있습니다.

- SOW(Statement of Work): 작업 명세서 등 별도 양식으로 작성된 문서  
- 사진 자료: 실험 사진, 회의 현장 사진 등  
- 기타 설계서: 도면, UI 설계안, 기능 흐름도 등  
- 외부 문서: 교수님 피드백 문서, 참고자료, 기타 팀 내부 자료 등

[주요 기능]  
- 파일 업로드: 사용자는 하나 이상의 파일을 선택하여 시스템에 업로드할 수 있습니다.  
- 파일 정보 저장: 파일명, 업로드 날짜 등이 자동으로 기록됩니다.  
- 파일 다운로드: 업로드된 파일은 필요할 때 언제든지 다운로드할 수 있습니다.  
- 파일 삭제: 불필요하거나 수정이 필요한 파일은 삭제할 수 있습니다.

[사용 팁]  
- 공식 산출물 외에 중요한 참고 자료나 내부 작업 파일이 있다면 이 메뉴를 적극 활용하시기 바랍니다.  
- 파일명에 내용을 요약해서 저장하면 팀원들이 쉽게 찾을 수 있습니다.
"""

manual_menu_3 = """
업무 관리  
메뉴 경로: 업무 관리

[기능 개요]  
‘업무 관리’는 프로젝트 내에서 발생하는 단기성 또는 비정형 작업을 등록하고 관리할 수 있는 기능입니다.  
‘업무 관리’ 메뉴는 WBS에 등록하기 애매하거나 소규모로 진행되는 작업들을 체계적으로 기록하고 추적하는 데 활용됩니다.

예를 들어 ‘다음 주 발표자료 만들기’, ‘회의록 작성’, ‘중간 보고 회의 준비’ 등  
정형화되지 않은 개별 업무들을 등록하여 관리할 수 있습니다.

[사용 목적 예시]  
- 중간/기말 발표자료 작성  
- 회의 자료 준비  
- 팀원 의견 수렴 회의 주최  
- 결과물 검토 및 수정 작업 등

[화면 구성 설명]

1. 업무 목록 테이블  
- 등록된 업무의 제목, 담당자, 일정, 완료 여부 등을 한눈에 확인할 수 있습니다.  
- ‘업무 수정’ 버튼을 클릭하면 해당 업무의 세부 정보 수정이 가능합니다.

2. 업무 추가  
- ‘업무 추가’ 버튼을 누르면 업무를 새로 등록할 수 있는 창이 나타납니다.  
- 입력 항목:  
  - 할일 제목  
  - 학생 선택  
  - 학번  
  - 시작일 / 종료일  
- ‘완료’ 버튼을 누르면 업무가 목록에 등록됩니다.

3. 업무 수정  
- 등록된 업무는 ‘업무 수정’ 버튼을 통해 내용 변경이 가능합니다.  
- 완료 여부는 업무를 처음 등록할 때가 아니라, 수정 화면에서만 체크할 수 있습니다.  
  (예: 작업이 끝난 뒤, ‘완료 여부’ 체크박스를 선택하여 상태를 갱신합니다.)  
- 필요 시 업무를 삭제할 수도 있습니다.

[주요 기능]  
- 업무 등록 / 수정 / 삭제  
- 담당자 지정  
- 업무 일정 관리  
- 완료 여부 설정 (※ 수정 화면에서 가능)

[사용 팁]  
- 짧은 기간 안에 수행되는 업무나, 반복되지 않는 개별 작업은 WBS보다 업무 관리 메뉴에서 관리하는 것이 더 효율적입니다.  
- 업무 완료 후에는 반드시 ‘업무 수정’에서 완료 여부를 체크하여 업무 상태를 최신으로 유지하시기 바랍니다.  
- 등록된 업무는 자동 저장되며, 추후 다시 열어볼 수 있습니다.
"""

manual_menu_4 = """
평가  
메뉴 경로: 평가

[기능 개요]  
‘평가’ 메뉴는 교수님 전용 기능으로, 프로젝트 종료 시 교수님이 학생들의 프로젝트를 항목별로 평가할 수 있도록 제공되는 기능입니다.  
학생 계정에서는 이 메뉴가 보이지 않으며, 교수님만 접근하여 평가를 입력하고 저장할 수 있습니다.

[사용 대상]  
- 교수 계정만 이용 가능  
- 학생 계정에서는 평가 메뉴가 비활성화되어 표시되지 않음

[주요 기능 설명]  
교수님은 아래 항목들을 기준으로 프로젝트를 수치화하여 평가할 수 있습니다. 각 항목은 100점 만점 기준으로 점수를 입력합니다.

- 기획 및 자료조사  
- 요구분석  
- 설계  
- 진척관리  
- 형상관리(버전)  
- 협력성(회의록)  
- 품질관리  
- 기술성  
- 발표  
- 완성도

[기능 안내]  
- 점수는 직접 입력할 수 있으며, 모든 항목 입력 후 ‘저장’ 버튼을 누르면 평가가 저장됩니다.  
- 저장된 평가는 시스템에 기록되어, 추후 확인이나 수정이 가능합니다.  
- ‘삭제’ 버튼을 누르면 현재 입력된 평가가 초기화됩니다.

[사용 팁]  
- 항목별로 점수를 입력할 때, 실제 프로젝트 결과물(산출물, 회의록, 업무 진행 상황 등)을 참고하시면 더 객관적인 평가가 가능합니다.  
- 팀 평가 외에 개인별 평가가 필요한 경우에는 별도로 수기 평가 또는 개별 메모 기능을 활용하시기 바랍니다.
"""

manual_menu_5 = """
프로젝트 관리  
메뉴 경로: 프로젝트 관리

[기능 개요]  
‘프로젝트 관리’는 프로젝트의 기본 정보 설정, 진행 상황 저장 및 복원, 삭제 기능 등을 제공하는 메뉴입니다.  
이 메뉴를 통해 프로젝트의 전체 흐름을 관리하고, 중요한 시점마다 저장하거나 과거 상태로 되돌릴 수 있습니다.

[기본 정보 수정]  
- 프로젝트 이름, 설명, 개발 방법론, 인원 수, 기간, 강의명, 담당 교수 등의 정보를 수정할 수 있습니다.  
- 모든 항목은 수정 후 ‘수정’ 버튼을 눌러 저장합니다.

[불러오기 / 저장하기 (구: 가져오기 / 내보내기)]  
이 기능은 GitHub의 커밋 기능처럼 특정 시점의 프로젝트 상태를 저장하고, 나중에 다시 불러올 수 있는 기능입니다.  
프로젝트를 진행하면서 분기점이나 중요한 변화가 있을 때 저장해두면, 다음과 같은 상황에서 유용하게 사용할 수 있습니다.

예시:  
- 실수로 산출물을 삭제했을 때  
- 개발 방향을 이전 상태로 되돌리고 싶을 때  
- 발표용 백업본을 따로 저장해두고 싶을 때  

▶ 저장하기 (프로젝트 저장하기 / 프로젝트 내보내기)  
- 현재 프로젝트의 진행 상태를 저장합니다.  
- 저장 시 변경사항에 대한 설명을 입력할 수 있으며, 저장된 시점은 ‘버전 목록’에 기록됩니다.  

▶ 불러오기  
- 저장된 이전 프로젝트 상태를 불러올 수 있습니다.  
- 원하는 버전을 선택하여 클릭하면 해당 시점으로 프로젝트가 되돌아갑니다.  
- 각 버전은 시간, 설명과 함께 나열되어 있어 관리가 용이합니다.

[프로젝트 삭제 및 복원]  
- 하단의 ‘프로젝트 삭제’ 영역에서 텍스트 박스에 `"삭제하겠습니다."`를 입력하고 삭제 버튼을 누르면 프로젝트가 삭제됩니다.  
- 실수로 프로젝트를 삭제했을 경우, 메인 메뉴의 ‘새로운 프로젝트’ > ‘프로젝트 복원’ 기능을 통해 최근 저장된 상태로 복원할 수 있습니다.  
  ※ 저장된 버전이 없을 경우 복원이 불가능하니, 중요한 작업 후에는 반드시 저장하기를 활용하시기 바랍니다.

[사용 팁]  
- 새로운 기능을 추가하거나 중요한 변경을 하기 전에는 반드시 저장하기(프로젝트 내보내기)를 통해 상태를 백업해두시기 바랍니다.  
- 버전별로 저장 설명을 남기면, 추후 어떤 시점에 어떤 변경이 있었는지 추적이 쉬워집니다.  
- 저장된 상태는 시간순 정렬되어 나열되며, 언제든지 되돌릴 수 있습니다.
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