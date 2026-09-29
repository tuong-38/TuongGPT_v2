from auth import hash_password, verify_password, create_access_token
from jose import jwt
import os

if __name__ == "__main__":
    print("--- KIỂM TRA MÃ HÓA & JWT ---")
    
    # 1. Thử nghiệm mã hóa mật khẩu
    raw_pass = "matkhau_bi_mat_123"
    hashed = hash_password(raw_pass)
    print(f"Mật khẩu gốc: {raw_pass}")
    print(f"Mật khẩu đã băm (Bcrypt): {hashed}")
    
    # Kiểm tra tính khớp
    assert verify_password(raw_pass, hashed) is True
    assert verify_password("sai_mat_khau", hashed) is False
    print(">> Kiểm tra băm và xác minh mật khẩu: CHÍNH XÁC!")

    # 2. Thử nghiệm tạo và giải mã JWT Token
    sample_payload = {"sub": "12345678-aaaa-bbbb-cccc-123456789abc", "username": "tuong_user"}
    token = create_access_token(sample_payload)
    print(f"\nToken mẫu được tạo:\n{token}")

    decoded = jwt.decode(token, os.getenv("JWT_SECRET_KEY", "tuonggpt_super_secret_key_2026"), algorithms=["HS256"])
    print(f"Dữ liệu giải mã thành công: {decoded}")
    print(">> Kiểm tra ký và giải mã JWT: CHÍNH XÁC!")