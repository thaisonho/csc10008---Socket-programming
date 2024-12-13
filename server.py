import socket
import threading
import os
from pathlib import Path
from users import UserManager

class FileTransferServer:
    def __init__(self, host='0.0.0.0', port=8386):
        self.host = host
        self.port = port
        self.user_manager = UserManager()
        self.active_users = {}
        self.shutdown_event = threading.Event()
        self.client_threads = []

    def start(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((self.host, self.port))
        server_socket.listen(5)
        
        print(f"Server đang chạy trên {self.host}:{self.port}")
        try:
            while not self.shutdown_event.is_set():
                try:
                    server_socket.settimeout(1.0)
                    client_socket, addr = server_socket.accept()
                except socket.timeout:
                    continue
                except OSError:
                    break  # Socket has been closed
                print(f"Đã kết nối từ {addr}")
                client_handler = threading.Thread(target=self.handle_client, args=(client_socket, addr))
                client_handler.start()
                self.client_threads.append(client_handler)
        except KeyboardInterrupt:
            print("Đang tắt server...")
            self.shutdown_event.set()
        finally:
            server_socket.close()
            # Wait for all client threads to finish
            for t in self.client_threads:
                t.join()

    def version_check(self, client_socket):
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

    def handle_client(self, client_socket, address):
        try:
            client_socket.settimeout(1.0)
            # Kiểm tra phiên bản giao thức
            self.version_check(client_socket)

            # Đăng nhập
            login_attempts = 3
            while self.active_users.get(address) is None and not self.shutdown_event.is_set():
                command_first = self.receive_message(client_socket)
                if self.shutdown_event.is_set():
                    self.send_message(client_socket, "SERVER_SHUTDOWN")
                    break
                if not command_first:
                    break
                if command_first.startswith("LOGIN"):
                    while login_attempts > 0:
                        parts = command_first.split('|')
                        if len(parts) != 3:
                            self.send_message(client_socket, "ERROR|Định dạng đăng nhập không hợp lệ")
                            break
                        username, password = parts[1], parts[2]
                        if self.user_manager.verify_user(username, password):
                            self.send_message(client_socket, "SUCCESS|Đăng nhập thành công")
                            self.active_users[address] = username
                            break
                        else:
                            self.send_message(client_socket, "ERROR|Tên đăng nhập hoặc mật khẩu không đúng")
                            login_attempts -= 1
                            break
                elif command_first.startswith("SIGNUP"):
                    while True:
                        parts = command_first.split('|')
                        if len(parts) != 3:
                            self.send_message(client_socket, "ERROR|Định dạng đăng ký không hợp lệ")
                            break
                        username, password = parts[1], parts[2]
                        if self.user_manager.user_exists(username):
                            self.send_message(client_socket, "ERROR|Người dùng đã tồn tại")
                            break
                        else:
                            if self.user_manager.add_user(username, password):
                                self.send_message(client_socket, "SUCCESS|Đăng ký thành công")
                                break
                            else:
                                self.send_message(client_socket, "ERROR|Đăng ký thất bại")
                                break
                else:
                    self.send_message(client_socket, "ERROR|Unknown command")

            if self.shutdown_event.is_set():
                self.send_message(client_socket, "SERVER_SHUTDOWN")
                return  # Exit the thread

            # Xử lý các lệnh sau khi đăng nhập thành công
            while not self.shutdown_event.is_set():
                command = self.receive_message(client_socket)
                if self.shutdown_event.is_set():
                    self.send_message(client_socket, "SERVER_SHUTDOWN")
                    break
                if not command:
                    break

                if command.startswith("UPLOAD"):
                    username = self.active_users[address]
                    storage_dir = self.user_manager.get_user_storage(username)
                    filename = command.split(' ', 1)[1]
                    self.send_message(client_socket, "FILENAME_OK")
                    
                    filesize_str = self.receive_message(client_socket)
                    try:
                        filesize = int(filesize_str)
                    except ValueError:
                        self.send_message(client_socket, "ERROR|Kích thước tệp tin không hợp lệ")
                        continue

                    self.send_message(client_socket, "READY")
                    
                    filepath = os.path.join(storage_dir, filename)
                    with open(filepath, 'wb') as f:
                        bytes_received = 0
                        while bytes_received < filesize and not self.shutdown_event.is_set():
                            try:
                                data = client_socket.recv(4096)
                            except socket.timeout:
                                continue
                            if not data:
                                break
                            f.write(data)
                            bytes_received += len(data)

                    if self.shutdown_event.is_set():
                        self.send_message(client_socket, "SERVER_SHUTDOWN")
                        break

                    if bytes_received == filesize:
                        self.send_message(client_socket, "SUCCESS")
                        print(f"Tải lên tệp tin: {filename} thành công từ {address}")
                    else:
                        self.send_message(client_socket, "ERROR|Tải lên không hoàn thành")

                elif command.startswith("LIST"):
                    username = self.active_users[address]
                    storage_dir = self.user_manager.get_user_storage(username)
                    files = os.listdir(storage_dir)
                    if not files:
                        self.send_message(client_socket, "ERROR|Không có tệp tin")
                    else:
                        file_info = []
                        for file in files:
                            filepath = os.path.join(storage_dir, file)
                            size = os.path.getsize(filepath)
                            file_info.append(f"{file}|{size}")
                        file_list = "\n".join(file_info)
                        self.send_message(client_socket, file_list)
                else:
                    self.send_message(client_socket, "ERROR|Unknown command")

            if self.shutdown_event.is_set():
                self.send_message(client_socket, "SERVER_SHUTDOWN")
                return  # Exit the thread

        except Exception as e:
            print(f"Lỗi khi xử lý client {address}: {e}")
        finally:
            if address in self.active_users:
                del self.active_users[address]
            client_socket.close()
            print(f"Đã ngắt kết nối với {address}")

    def send_message(self, client_socket, message):
        message = f"{message}\n"
        try:
            client_socket.sendall(message.encode())
        except Exception as e:
            print(f"Error sending message: {e}")

    def receive_message(self, client_socket):
        data = ''
        try:
            while not data.endswith('\n') and not self.shutdown_event.is_set():
                try:
                    packet = client_socket.recv(4096).decode()
                except socket.timeout:
                    continue
                if not packet:
                    break
                data += packet
        except Exception as e:
            print(f"Error receiving message: {e}")
            return ''
        return data.strip()

if __name__ == "__main__":
    server = FileTransferServer()
    server.start()
