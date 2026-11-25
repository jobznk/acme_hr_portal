from dataclasses import asdict
from fastapi import FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel
from langchain_groq import ChatGroq
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings

from config import (
    COMPANY_NAME,
    POLICY_FILE,
    DATABASE_URL,
    EMBEDDING_MODEL,
    GROQ_API_KEY,
    GROQ_MODEL,
)
from repositories.employee_repo import EmployeeRepository
from repositories.policy_repo import PolicyRepository
from services.auth_service import AuthService
from services.rag_service import HRChatService

app = FastAPI(title=f"{COMPANY_NAME} HR AI Backend", version="3.0.0")

# Initialize DB pool & AI models ONCE when FastAPI starts
employee_repo = EmployeeRepository(db_url=DATABASE_URL)
auth_service = AuthService(employee_repo=employee_repo)

embeddings = FastEmbedEmbeddings(model_name=EMBEDDING_MODEL)
llm = ChatGroq(model=GROQ_MODEL, api_key=GROQ_API_KEY, temperature=0)
policy_repo = PolicyRepository(
    db_url=DATABASE_URL,
    embedding_function=embeddings,
    initial_policy_file=POLICY_FILE,
)
chat_service = HRChatService(
    policy_repo=policy_repo,
    employee_repo=employee_repo,
    llm=llm,
)


class LoginRequest(BaseModel):
    emp_id: str
    password: str


class RegisterRequest(BaseModel):
    emp_id: str
    name: str
    role: str
    location: str
    password: str


class ChatRequest(BaseModel):
    emp_id: str
    prompt_text: str


@app.get("/health")
def health_check():
    return {"status": "ok", "service": f"{COMPANY_NAME} HR FastAPI Backend"}


@app.post("/auth/login")
def login(payload: LoginRequest):
    employee = auth_service.login(payload.emp_id, payload.password)
    if not employee:
        raise HTTPException(status_code=401, detail="Invalid Employee ID or Password.")
    return {"employee": asdict(employee)}


@app.post("/auth/register")
def register(payload: RegisterRequest):
    success, message = auth_service.register(
        payload.emp_id, payload.name, payload.role, payload.location, payload.password
    )
    if not success:
        raise HTTPException(status_code=400, detail=message)
    return {"message": message}


@app.get("/employees/{emp_id}")
def get_employee(emp_id: str):
    employee = employee_repo.get_employee_by_id(emp_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found.")
    return {"employee": asdict(employee)}


@app.post("/chat/ask")
async def ask_agent(payload: ChatRequest):
    employee = employee_repo.get_employee_by_id(payload.emp_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found.")
    reply = await chat_service._ask_mcp_agent(payload.prompt_text, employee)
    return {"reply": reply}


@app.post("/docs/upload")
async def upload_document(file: UploadFile = File(...)):
    file_bytes = await file.read()
    chunks = chat_service.upload_policy_document(file.filename, file_bytes)
    return {"filename": file.filename, "chunks_indexed": chunks}
