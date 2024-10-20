# 계정/세션 관련 기능
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

router = APIRouter()

class SignUp_Payload(BaseModel):
    is_student: bool
    name: str
    univ_id: int
    email: str
    id: str
    pw: str
    department: int

@router.get("/acc_signup")
async def api_acc_signup_get():
    return {"Message": "Please use post method, not get method."}

@router.post("/acc_signup")
async def api_acc_signup_post(payload: SignUp_Payload):
    """
    필요시 payload의 유효성 검토..
    """
    return payload

class Signin_Payload(BaseModel):
    id: str
    pw: str

@router.get("/acc_signin")
async def api_acc_signin_get():
    return {"Message": "OK"}

@router.post("/acc_signin")
async def api_acc_signin_post(payload: Signin_Payload):
    """
    MySQL과 연동하여 계정 확인 후 로그인 성공 여부 확인
    아래는 post가 작동하는지 확인하기 위한 코드
    """
    valid_id = "nsu"
    valid_pw = "asd1234"
    token = "Ack2jb028173920!"

    if payload.id == valid_id and payload.pw == valid_pw:
        return {"login": "True", "Token": token}
    else:
        return JSONResponse(status_code=401, content={"login": "failed"})
