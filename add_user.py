from users import UserManager

def main():
    um = UserManager()
    username = input("Nhập tên người dùng: ")
    while um.user_exists(username):
        print("Người dùng đã tồn tại. Vui lòng nhập tên người dùng khác.")
        username = input("Nhập tên người dùng: ")
    password = input("Nhập mật khẩu: ")

    if um.add_user(username, password):
        print(f"Thêm người dùng '{username}' thành công.")
    else:
        print(f"Error: Người dùng")

if __name__ == "__main__":
    main()
