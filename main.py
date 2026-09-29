import json
import os
import shutil
import time
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, UploadFile, File, Form, Request, Depends, HTTPException, status, Query
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy.orm import Session
from langchain_core.messages import HumanMessage, ToolMessage
from jose import jwt, JWTError

from database import (
    init_db,
    get_db,
    User,
    create_or_update_conversation,
    list_conversations,
    get_chat_history,
    save_chat_message,
    delete_conversation_by_thread_id,
)
from auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
    SECRET_KEY,
    ALGORITHM,
)
from rag import add_document_to_rag
from agent import get_agent

# Khởi tạo bảng dữ liệu trên Supabase nếu chưa có
init_db()

app = FastAPI(title="TuongGPT Multi-tenant API")
templates = Jinja2Templates(directory="templates")

Path("uploads").mkdir(exist_ok=True)
Path("templates").mkdir(exist_ok=True)


# --- Schemas xác thực ---
class AuthRequest(BaseModel):
    username: str
    password: str


# --- Helper: Xác thực Token riêng cho luồng SSE Stream ---
def get_user_from_token_str(token: str, db: Session) -> User:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Token không hợp lệ.")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token không hợp lệ hoặc đã hết hạn.")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="Người dùng không tồn tại.")
    return user


def extract_text_content(content) -> str:
    """Extract the plain text string from the LangChain/Gemini content."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        extracted = []
        for part in content:
            if isinstance(part, dict) and part.get("type") == "text":
                extracted.append(part.get("text", ""))
            elif isinstance(part, str):
                extracted.append(part)
        return "".join(extracted)
    return ""


# ==================== ROUTE GIAO DIỆN & AUTH ====================

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")


@app.post("/api/auth/register")
def register(req: AuthRequest, db: Session = Depends(get_db)):
    clean_username = req.username.strip()
    if len(clean_username) < 3:
        raise HTTPException(status_code=400, detail="Tên đăng nhập tối thiểu 3 ký tự.")
    if len(req.password) < 6:
        raise HTTPException(status_code=400, detail="Mật khẩu tối thiểu 6 ký tự.")

    existing_user = db.query(User).filter(User.username == clean_username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Tên người dùng này đã tồn tại. Hãy chọn tên khác.")

    new_user = User(
        username=clean_username,
        hashed_password=hash_password(req.password)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    token = create_access_token({"sub": str(new_user.id), "username": new_user.username})
    return {"access_token": token, "token_type": "bearer", "username": new_user.username}


@app.post("/api/auth/login")
def login(req: AuthRequest, db: Session = Depends(get_db)):
    clean_username = req.username.strip()
    user = db.query(User).filter(User.username == clean_username).first()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Tên đăng nhập hoặc mật khẩu không chính xác.")

    token = create_access_token({"sub": str(user.id), "username": user.username})
    return {"access_token": token, "token_type": "bearer", "username": user.username}


# ==================== ROUTE QUẢN LÝ PHIÊN CHAT ====================

@app.get("/api/conversations")
def api_get_conversations(current_user: User = Depends(get_current_user)):
    conversations = list_conversations(str(current_user.id))
    return [
        {
            "thread_id": conv.thread_id,
            "title": conv.title,
            "updated_at": conv.updated_at.isoformat() if conv.updated_at else ""
        }
        for conv in conversations
    ]


@app.get("/api/chat-history/{thread_id}")
def api_get_history(thread_id: str, current_user: User = Depends(get_current_user)):
    history = get_chat_history(str(current_user.id), thread_id)
    return [{"role": msg.role, "content": msg.content} for msg in history]


@app.delete("/api/conversations/{thread_id}")
def api_delete_conversation(thread_id: str, current_user: User = Depends(get_current_user)):
    success = delete_conversation_by_thread_id(str(current_user.id), thread_id)
    return {"status": "success" if success else "error"}


@app.post("/api/upload")
async def api_upload_file(
    file: UploadFile = File(...),
    thread_id: str = Form(...),
    current_user: User = Depends(get_current_user)
):
    save_path = Path("uploads") / file.filename
    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        # Cách ly tệp nạp theo cả user_id và thread_id
        result = add_document_to_rag(str(save_path), str(current_user.id), thread_id)
        return {"status": "success", "data": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ==================== LUỒNG TRUYỀN PHÁT SSE STREAM ====================

@app.get("/api/chat-stream")
def api_chat_stream(
    thread_id: str,
    message: str,
    token: str = Query(...),
    model_name: str = "gemini-3.5-flash-lite",
    db: Session = Depends(get_db)
):
    # Xác thực token từ query parameter của EventSource
    user = get_user_from_token_str(token, db)
    user_id_str = str(user.id)

    create_or_update_conversation(user_id_str, thread_id, first_message=message)
    save_chat_message(user_id_str, thread_id, role="user", content=message)

    agent = get_agent(model_name)
    # Truyền context an toàn qua LangGraph config, loại bỏ triệt để biến toàn cục
    config = {
        "configurable": {
            "thread_id": thread_id,
            "user_id": user_id_str
        }
    }

    def event_generator():
        full_content = ""
        try:
            for message_chunk, metadata in agent.stream(
                {"messages": [HumanMessage(content=message)]},
                config=config,
                stream_mode="messages"
            ):
                if isinstance(message_chunk, ToolMessage):
                    continue
                if getattr(message_chunk, "tool_call_chunks", None):
                    continue

                raw_content = getattr(message_chunk, "content", "")
                text_chunk = extract_text_content(raw_content)

                if text_chunk:
                    full_content += text_chunk
                    yield f"data: {json.dumps({'chunk': text_chunk})}\n\n"
                    time.sleep(0.02)  # Nhịp mượt văn bản

            if full_content.strip():
                save_chat_message(user_id_str, thread_id, role="assistant", content=full_content)

            yield f"data: {json.dumps({'done': True})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")