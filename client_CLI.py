import os
import sys
import getpass
from client.transfer import FileTransferClient
from tqdm import tqdm

class ClientCLI:
    def __init__(self):
        self.client = FileTransferClient()
        self.username = None
        self.is_running = True

    def connect(self):
        try:
            self.client.connect()
            print("Đã kết nối tới server thành công!")
            return True
        except Exception as e:
            print(f"Lỗi kết nối: {e}")
            return False
    def signup(self):
        username = input("Nhập tên người dùng: ")
        if username == "":
            print("Tên người dùng không được để trống!")
            return
        password = getpass.getpass("Nhập mật khẩu: ")
        if password == "":
            print("Mật khẩu không được để trống!")
            return
        confirm_password = getpass.getpass("Nhập lại mật khẩu: ")

        if password != confirm_password:
            print("Mật khẩu không khớp!")
            return

        try:
            if self.client.signup(username, password):
                print(f"Đã tạo người dùng '{username}' thành công.")
            else:
                print("Người dùng đã tồn tại.")
        except Exception as e:
            print(f"Lỗi tạo người dùng: {e}")
    def login(self):
        # cho phép người dùng chọn đăng nhậpnhập
        attempts = 3
        while attempts > 0:
            try:
                username = input("Tên đăng nhập: ")
                password = getpass.getpass("Mật khẩu: ")
                
                if self.client.login(username, password):
                    self.username = username
                    print("Đăng nhập thành công!")
                    return True
            except Exception as e:
                print(f"Lỗi đăng nhập: {e}")
                attempts -= 1
                if attempts > 0:
                    print(f"Còn {attempts} lần thử")
        
        return False

    def show_help(self):
        print("\nDanh sách lệnh:")
        print("  upload <đường dẫn file>  - Tải file lên server")
        print("  download <tên file>      - Tải file từ server")
        print("  list                     - Xem danh sách file")
        print("  help                     - Hiển thị trợ giúp") 
        print("  exit                     - Thoát chương trình")

    def progress_callback(self, progress):
        self.progress_bar.update(progress - self.progress_bar.n)

    def upload_file(self, filepath):
        try:
            if not os.path.exists(filepath):
                print(f"Không tìm thấy file: {filepath}")
                return

            filesize = os.path.getsize(filepath)
            filename = os.path.basename(filepath)

            print(f"\nĐang tải lên {filename} ({filesize} bytes)")
            self.progress_bar = tqdm(total=100, desc="Tiến độ")
            
            self.client.upload_file(filepath, self.progress_callback)
            self.progress_bar.close()
            print("Tải lên thành công!")

        except Exception as e:
            print(f"Lỗi tải lên: {e}")

    def download_file(self, filename):
        try:
            save_path = os.path.join(os.getcwd(), filename)
            print(f"\nĐang tải xuống {filename}")
            self.progress_bar = tqdm(total=100, desc="Tiến độ")
            
            self.client.download_file(filename, save_path, self.progress_callback)
            self.progress_bar.close()
            print(f"Đã tải xuống thành công vào: {save_path}")

        except Exception as e:
            print(f"Lỗi tải xuống: {e}")

    def list_files(self):
        try:
            files = self.client.list_files()
            if not files:
                print("Không có file nào")
                return

            print("\nDanh sách file:")
            for file_info in files:
                if "|" in file_info:
                    name, size = file_info.split("|")
                    print(f"  {name:<30} {int(size):>10} bytes")
                else:
                    print(f"  {file_info}")

        except Exception as e:
            print(f"Lỗi lấy danh sách file: {e}")

    def handle_server_shutdown(self):
        print("\nServer đã ngắt kết nối!")
        self.is_running = False

    

    def run(self):
        if not self.connect():
            return

        self.client.set_shutdown_callback(self.handle_server_shutdown)

        os.system('cls' if os.name == 'nt' else 'clear')
        
        while True:
            print("\nChọn một trong các lựa chọn sau:")
            print("  1. Đăng ký")
            print("  2. Đăng nhập")
            print("  3. Thoát")

            choice = input("> ").strip()
            if choice == "1":
                self.signup()
            elif choice == "2":
                if self.login():
                    break
            elif choice == "3":
                return
            else:
                print("Lựa chọn không hợp lệ!")

        self.show_help()

        while self.is_running:
            try:
                command = input("\n> ").strip()
                
                if not command:
                    continue

                parts = command.split()
                cmd = parts[0].lower()

                if cmd == "exit":
                    break
                elif cmd == "chat":
                    self.chat_mode()
                elif cmd == "help":
                    self.show_help()
                elif cmd == "list":
                    self.list_files()
                elif cmd == "upload" and len(parts) > 1:
                    self.upload_file(parts[1])
                elif cmd == "download" and len(parts) > 1:
                    self.download_file(parts[1])
                else:
                    print("Lệnh không hợp lệ! Gõ 'help' để xem hướng dẫn")

            except KeyboardInterrupt:
                print("\nĐang thoát...")
                break
            except Exception as e:
                print(f"Lỗi: {e}")

        self.client.close()
        print("Đã ngắt kết nối")

if __name__ == "__main__":
    cli = ClientCLI()
    cli.run()