import os
import sys
from pathlib import Path
import pytest

# Tự động trỏ đường dẫn về thư mục gốc của dự án để Python tìm thấy file auth.py
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Thiết lập biến môi trường giả lập cho test
os.environ["JWT_SECRET_KEY"] = "super_secret_test_key_ci_pipeline_2026"
os.environ["JWT_ALGORITHM"] = "HS256"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "30"

from auth import hash_password, verify_password, create_access_token, SECRET_KEY, ALGORITHM
from jose import jwt


def test_password_hashing():
    """Kiểm tra logic băm và xác thực mật khẩu"""
    password = "MySecurePassword123!"
    hashed = hash_password(password)

    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("WrongPassword456!", hashed) is False


def test_jwt_token_generation_and_decoding():
    """Kiểm tra tạo token JWT và giải mã payload"""
    user_payload = {"sub": "user_123456", "username": "tuong_tester"}
    token = create_access_token(user_payload)

    assert isinstance(token, str)
    assert len(token) > 0

    decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    assert decoded.get("sub") == "user_123456"
    assert decoded.get("username") == "tuong_tester"
    assert "exp" in decoded

# Thiết lập biến môi trường giả lập cho test
os.environ["DATABASE_URL"] = "sqlite:///./test_ci.db"
os.environ["JWT_SECRET_KEY"] = "super_secret_test_key_ci_pipeline_2026"
os.environ["JWT_ALGORITHM"] = "HS256"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "30"