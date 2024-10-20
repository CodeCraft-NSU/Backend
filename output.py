# 산출물 관련 기능
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import mysql_connection  # MySQL 연결 기능 수행

router = APIRouter()

class summary_document_add(BaseModel): # 개요서 간단본 추가 클래스
    pname: str # 프로젝트 제목
    pteam: str # 팀 구성
    psummary: str # 프로젝트 개요
    pstart: str # 일정 시작일
    pend: str # 일정 종료일
    prange: str # 프로젝트 범위
    poutcomes: str # 기대 성과

class overview_document_add(BaseModel): # 개요서 상세본 추가 클래스
    poverview: str # 프로젝트 개요
    pteam: str # 팀 구성 및 역할 분담
    pgoals: str # 세부 목표
    pstart: str # 일정 시작일
    pend: str # 일정 종료일
    prange: str # 프로젝트 범위
    pstack: str # 기술 스택 및 도구

class meeting_minutes_add(BaseModel):  # 회의록 추가 클래스
    main_agenda: str  # 주요 안건
    date_time: str  # 일시
    location: str  # 장소
    participants: str  # 참여자
    responsible_person: str  # 책임자
    meeting_content: str  # 회의 내용
    meeting_outcome: str  # 회의 결과

class ReqSpecAdd(BaseModel):  # Requirements Specification Addition Class
    # 기능 요구사항
    feature_name: str # 이름
    description: str # 설명
    priority: int # 우선 순위
    # 비기능 요구사항
    non_functional_requirement_name: str # 이름
    non_functional_description: str # 설명
    non_functional_priority: int # 우선순위
    # 시스템 요구사항
    system_item: str # 항목
    system_description: str # 설명