import os
import uuid
from datetime import datetime
from dotenv import load_dotenv

from sqlalchemy import create_engine, Column, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    DATABASE_URL = "sqlite:///./test_fallback.db"

# Nếu dùng SQLite fallback thì bỏ check args của postgres
connect_args = {"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Tạo engine kết nối PostgreSQL trên Supabase với cơ chế giữ kết nối ổn định
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,      # Tự động kiểm tra kết nối còn sống trước khi query
    pool_recycle=300,        # Tái chế kết nối mỗi 5 phút để tránh Supabase ngắt kết nối idle
    pool_size=5,             # Giới hạn số connection mở sẵn
    max_overflow=10
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


# 1. Bảng User: Tối giản, không chứa thông tin cá nhân
class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Quan hệ 1-N với hội thoại
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")


# 2. Bảng Conversation: Gắn chặt với user_id
class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    thread_id = Column(String(100), unique=True, nullable=False, index=True)
    title = Column(String(255), default="Cuộc trò chuyện mới")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="conversations")
    messages = relationship("ChatMessage", back_populates="conversation", cascade="all, delete-orphan")


# 3. Bảng ChatMessage: Lịch sử tin nhắn của từng phiên
class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    thread_id = Column(String(100), ForeignKey("conversations.thread_id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # 'user' hoặc 'assistant'
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    conversation = relationship("Conversation", back_populates="messages")


# 4. Bảng LongTermMemory: Ký ức dài hạn theo người dùng & phiên
class LongTermMemory(Base):
    __tablename__ = "long_term_memory"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    thread_id = Column(String(100), nullable=False, index=True)
    memory = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


# Dependency hỗ trợ FastAPI lấy DB Session an toàn
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Tự động tạo toàn bộ các bảng trên Supabase PostgreSQL nếu chưa có."""
    Base.metadata.create_all(bind=engine)


def save_memory(user_id: str, thread_id: str, memory: str) -> str:
    """Save long-term memory tied to a specific user_id and thread_id."""
    db = SessionLocal()
    try:
        item = LongTermMemory(
            user_id=user_id,
            thread_id=thread_id,
            memory=memory,
            created_at=datetime.utcnow()
        )
        db.add(item)
        db.commit()
        return "Memory saved successfully."
    except Exception as e:
        db.rollback()
        return f"Error saving memory: {str(e)}"
    finally:
        db.close()


def search_memory(user_id: str, thread_id: str, query: str = "") -> str:
    """Search long-term memories belonging to a specific user_id and thread_id."""
    db = SessionLocal()
    try:
        memories = (
            db.query(LongTermMemory)
            .filter(
                LongTermMemory.user_id == user_id,
                LongTermMemory.thread_id == thread_id
            )
            .order_by(LongTermMemory.created_at.desc())
            .limit(20)
            .all()
        )
        if not memories:
            return "No saved memory found for this user/thread."
        return "\n".join([f"- {m.memory}" for m in memories])
    finally:
        db.close()

def create_or_update_conversation(user_id: str, thread_id: str, first_message: str | None = None):
    """Create or update session time for a specific user."""
    db = SessionLocal()
    try:
        conversation = (
            db.query(Conversation)
            .filter(Conversation.user_id == user_id, Conversation.thread_id == thread_id)
            .first()
        )

        if not conversation:
            title = "Cuộc trò chuyện mới"
            if first_message:
                title = first_message.strip()[:40]
                if len(first_message.strip()) > 40:
                    title += "..."

            conversation = Conversation(
                user_id=user_id,
                thread_id=thread_id,
                title=title,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            db.add(conversation)
        else:
            conversation.updated_at = datetime.utcnow()

        db.commit()
    finally:
        db.close()


def list_conversations(user_id: str):
    """List the conversations belonging solely to that user_id."""
    db = SessionLocal()
    try:
        return (
            db.query(Conversation)
            .filter(Conversation.user_id == user_id)
            .order_by(Conversation.updated_at.desc())
            .all()
        )
    finally:
        db.close()


def save_chat_message(user_id: str, thread_id: str, role: str, content: str):
    """Save the chat message and update the session's updated_at timestamp."""
    db = SessionLocal()
    try:
        msg = ChatMessage(
            thread_id=thread_id,
            role=role,
            content=content,
            created_at=datetime.utcnow()
        )
        db.add(msg)

        conversation = (
            db.query(Conversation)
            .filter(Conversation.user_id == user_id, Conversation.thread_id == thread_id)
            .first()
        )
        if conversation:
            conversation.updated_at = datetime.utcnow()

        db.commit()
    finally:
        db.close()


def get_chat_history(user_id: str, thread_id: str):
    """Get all chat history of a session belong to an user_id."""
    db = SessionLocal()
    try:
        # Kiểm tra quyền sở hữu thread
        conversation = (
            db.query(Conversation)
            .filter(Conversation.user_id == user_id, Conversation.thread_id == thread_id)
            .first()
        )
        if not conversation:
            return []

        return (
            db.query(ChatMessage)
            .filter(ChatMessage.thread_id == thread_id)
            .order_by(ChatMessage.created_at.asc())
            .all()
        )
    finally:
        db.close()


def delete_conversation_by_thread_id(user_id: str, thread_id: str) -> bool:
    """Automatically delete a session."""
    db = SessionLocal()
    try:
        conversation = (
            db.query(Conversation)
            .filter(Conversation.user_id == user_id, Conversation.thread_id == thread_id)
            .first()
        )
        if not conversation:
            return False

        db.delete(conversation)
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        print(f"Lỗi khi xóa hội thoại: {e}")
        return False
    finally:
        db.close()