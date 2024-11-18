# add_user.py
from users import UserManager

def main():
    um = UserManager()
    username = input("Nhập tên người dùng: ")
    password = input("Nhập mật khẩu: ")
    storage_dir = input("Nhập thư mục lưu trữ (nhấn Enter để sử dụng mặc định): ").strip()
    storage_dir = storage_dir if storage_dir else None

    if um.add_user(username, password, storage_dir):
        print(f"Thêm người dùng '{username}' thành công.")
    else:
        print(f"Người dùng '{username}' đã tồn tại.")

if __name__ == "__main__":
    main()