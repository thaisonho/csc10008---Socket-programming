import socket
import threading
import os
from pathlib import Path
from users import UserManager

class FileTransferServer:
    def __init__(self, host='0.0.0.0', port=5000):
        self.host = host
        self.port = port
        self.storage_dir = "server_storage"
        os.makedirs(self.storage_dir, exist_ok=True)
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.user_manager = UserManager()
        self.active_users = {}

    def start(self):
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        print(f"Server đang chạy trên {self.host}:{self.port}")
        try:
            while True:
                client_socket, addr = self.server_socket.accept()
                print(f"Đã kết nối từ {addr}")
                client_handler = threading.Thread(target=self.handle_client, args=(client_socket, addr))
                client_handler.start()
        except KeyboardInterrupt:
            print("Đang tắt server...")
        finally:
            self.server_socket.close()

    def handle_client(self, client_socket, address):
        try:
            # Kiểm tra phiên bản giao thức
            version_msg = self.receive_message(client_socket)
            if version_msg.startswith("VERSION"):
                client_version = version_msg.split()[1]
                if client_version == "1.0":
                    self.send_message(client_socket, "VERSION_OK")
                else:
                    self.send_message(client_socket, "VERSION_ERROR")
                    client_socket.close()
                    return
            else:
                self.send_message(client_socket, "VERSION_ERROR")
                client_socket.close()
                return

            # Đăng nhập
            login_attempts = 3
            while login_attempts > 0:
                command = self.receive_message(client_socket)
                if command.startswith("LOGIN"):
                    parts = command.split('|')
                    if len(parts) != 3:
                        self.send_message(client_socket, "ERROR|Định dạng đăng nhập không hợp lệ")
                        continue
                    username, password = parts[1], parts[2]
                    if self.user_manager.verify_user(username, password):
                        self.send_message(client_socket, "SUCCESS|Đăng nhập thành công")
                        self.active_users[address] = username
                        break
                    else:
                        login_attempts -= 1
                        self.send_message(client_socket, f"ERROR|Tên đăng nhập hoặc mật khẩu không đúng. Còn {login_attempts} lần thử.")
                else:
                    self.send_message(client_socket, "ERROR|Phải đăng nhập trước khi thực hiện")
            else:
                self.send_message(client_socket, "ERROR|Quá số lần đăng nhập")
                client_socket.close()
                return

            # Xử lý các lệnh sau khi đăng nhập thành công
            while True:
                command = self.receive_message(client_socket)
                if not command:
                    break

                if command.startswith("UPLOAD"):
                    filename = command.split(' ', 1)[1]
                    self.send_message(client_socket, "FILENAME_OK")
                    
                    filesize_str = self.receive_message(client_socket)
                    try:
                        filesize = int(filesize_str)
                    except ValueError:
                        self.send_message(client_socket, "ERROR|Kích thước tệp tin không hợp lệ")
                        continue

                    self.send_message(client_socket, "READY")
                    
                    filepath = os.path.join(self.storage_dir, filename)
                    with open(filepath, 'wb') as f:
                        bytes_received = 0
                        while bytes_received < filesize:
                            data = client_socket.recv(4096)
                            if not data:
                                break
                            f.write(data)
                            bytes_received += len(data)

                    if bytes_received == filesize:
                        self.send_message(client_socket, "SUCCESS")
                        print(f"Tàng lên tệp tin: {filename} thành công từ {address}")
                    else:
                        self.send_message(client_socket, "ERROR|Tải lên không hoàn thành")

                elif command.startswith("DOWNLOAD"):
                    filename = command.split(' ', 1)[1]
                    filepath = os.path.join(self.storage_dir, filename)
                    if os.path.exists(filepath):
                        filesize = os.path.getsize(filepath)
                        self.send_message(client_socket, str(filesize))
                        
                        ready = self.receive_message(client_socket)
                        if ready == "READY":
                            with open(filepath, 'rb') as f:
                                while True:
                                    data = f.read(4096)
                                    if not data:
                                        break
                                    client_socket.sendall(data)
                            # Đảm bảo gửi SUCCESS sau khi gửi xong dữ liệu
                            self.send_message(client_socket, "SUCCESS\n")
                            print(f"Tải xuống tệp tin: {filename} thành công đến {address}")
                        else:
                            self.send_message(client_socket, "ERROR|Client không sẵn sàng")
                    else:
                        self.send_message(client_socket, "FILE_NOT_FOUND")

                elif command == "LIST":
                    files = os.listdir(self.storage_dir)
                    if not files:
                        self.send_message(client_socket, "ERROR|Không có tệp tin")
                    else:
                        file_list = "\n".join([f"{f}|{os.path.getsize(os.path.join(self.storage_dir, f))}" for f in files])
                        self.send_message(client_socket, file_list)
                
                else:
                    self.send_message(client_socket, "ERROR|Lệnh không hợp lệ")

        except Exception as e:
            print(f"Lỗi khi xử lý client {address}: {e}")
        finally:
            if address in self.active_users:
                del self.active_users[address]
            client_socket.close()
            print(f"Đã ngắt kết nối với {address}")

    def send_message(self, client_socket, message):
        try:
            message = f"{message}\n"
            client_socket.sendall(message.encode())
        except Exception as e:
            print(f"Lỗi gửi tin nhắn: {e}")

    def receive_message(self, client_socket):
        try:
            data = ''
            while not data.endswith('\n'):
                packet = client_socket.recv(4096).decode()
                if not packet:
                    break
                data += packet
            return data.strip()
        except Exception as e:
            print(f"Lỗi nhận tin nhắn: {e}")
            return ''

if __name__ == "__main__":
    server = FileTransferServer()
    server.start()