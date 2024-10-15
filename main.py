from fastapi import FastAPI
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import mysql_connection, json

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "root of PMS Project API."}

@app.get("/api")
async def api_root():
    return {"Useage Example": "To Be Determined."}

@app.get("/api/acc_signup")
async def api_acc_signup_get():
    return {"Message": "Please use post method, not get method."}

class Signin_Payload(BaseModel):
    id: str
    pw: str

class SignUp_Payload(BaseModel):
    id: str
    pw: str

@app.post("/api/acc_signup")
async def api_acc_signup_post(payload: SignUp_Payload):
    """
    필요시 payload의 유효성 검토..
    """
    return payload.dict()

@app.get("/api/acc_signin")
async def api_acc_signin_get():
    return {"Message": "OK"}

@app.post("/api/acc_signin")
async def api_acc_signin_post(payload: Signin_Payload):
    """
    MySQL과 연동하여 계정 확인 후 로그인 성공 여부 확인
    아래는 post가 작동하는지 확인하기 위한 코드
    """
    valid_id = "nsu"
    valid_pw = "asd1234"

    if payload.id == valid_id and payload.pw == valid_pw:
        return {"login": "True", "Token": "..."}
    else:
        return JSONResponse(status_code=401, content={"login": "failed"})