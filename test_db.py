from database import init_db, engine

if __name__ == "__main__":
    print("Đang kết nối đến Supabase PostgreSQL...")
    try:
        init_db()
        print("TẠO BẢNG THÀNH CÔNG! Đã kết nối Supabase hoàn tất.")
    except Exception as e:
        print("KẾT NỐI THẤT BẠI:")
        print(e)