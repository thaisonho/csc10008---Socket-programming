import socket
import threading
import os
from pathlib import Path
from users import UserManager
import hashlib
import requests
import logging
import datetime

LOG_DIR = 'logs'
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

log_file = os.path.join(LOG_DIR, f'server_{datetime.datetime.now().strftime('%d%m%Y_%H%M%S')}.log')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

class FileTransferServer:
    def __init__(self, host='0.0.0.0', port=8386):
        self.host = host
        self.port = port
        self.user_manager = UserManager()
        self.active_users = {}
        self.shutdown_event = threading.Event()
        self.client_threads = []
        self.server_socket = None
        logging.info(f'Server initialized')
        
    def generate_file_checksum(self, file_path):
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def start(self):
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            self.server_socket.settimeout(1.0)
            
            logging.info(f'Server running on {self.host}:{self.port}')
            logging.info(f'Local IP address: {self.get_local_ip()}')
            logging.info(f'Public IP address: {self.get_public_ip()}')
            print(f"Server đang chạy trên {self.host}:{self.port}")
            local_ip = self.get_local_ip()
            public_ip = self.get_public_ip()
            print(f"Địa chỉ IP local: {local_ip}")
            print(f"Địa chỉ IP public: {public_ip}")

            while not self.shutdown_event.is_set():
                try:
                    client_socket, addr = self.server_socket.accept()
                    print(f"Đã kết nối từ {addr}")
                    logging.info(f"New connection accepted from {addr}")
                    client_handler = threading.Thread(
                        target=self.handle_client, 
                        args=(client_socket, addr),
                        daemon=True
                    )
                    client_handler.start()
                    self.client_threads.append(client_handler)
                except socket.timeout:
                    continue
                except OSError:
                    break

        except KeyboardInterrupt:
            logging.info("Keyboard interrupt received")
            print("Server shutdown initiated by keyboard interrupt")
        except Exception as e:
            logging.error(f"Unexpected error: {str(e)}")
        finally:
            # Ensure shutdown is called and logs are flushed
            self.shutdown()
            for handler in logging.getLogger().handlers:
                handler.flush()

    def shutdown(self):
        try:
            logging.info('Starting server shutdown sequence...')
            print('Server is closing...\n')
            self.shutdown_event.set()

            # Notify all clients
            for addr, username in list(self.active_users.items()):
                try:
                    client_socket = next(
                        thread._args[0] for thread in self.client_threads
                        if thread._args[1] == addr
                    )
                    self.send_message(client_socket, "SERVER_SHUTDOWN")
                    logging.info(f'Notified client {username} at {addr} about shutdown')
                except Exception as e:
                    logging.error(f'Failed to notify client {addr}: {str(e)}')
                    print(f'Không thể thông báo cho client {addr} về việc tắt server: {e}')
                    
            # Close server socket
            if self.server_socket:
                try:
                    self.server_socket.close()
                    logging.info('Server socket closed')
                except Exception as e:
                    logging.error(f'Error closing server socket: {str(e)}')
            
            # Clean up active users
            for addr in list(self.active_users.keys()):
                if addr in self.active_users:
                    logging.info(f'Removing active user at {addr}')
                    del self.active_users[addr]
            
            # Join client threads
            for thread in self.client_threads:
                try:
                    thread.join(timeout=2.0)
                    logging.info(f'Client thread joined: {thread.name}')
                except Exception as e:
                    logging.error(f'Error joining thread {thread.name}: {str(e)}')
            
            logging.info('Server shutdown completed')
            print('Server đã tắt')
            
            # Ensure all logs are written
            for handler in logging.getLogger().handlers:
                handler.flush()
                handler.close()
                
        except Exception as e:
            logging.critical(f'Unexpected error during shutdown: {str(e)}')
            raise

    def version_check(self, client_socket):
        version_msg = self.receive_message(client_socket)
        if version_msg.startswith("VERSION"):
            client_version = version_msg.split()[1]
            if client_version == "1.0":
                self.send_message(client_socket, "VERSION_OK")
                return True
            else:
                self.send_message(client_socket, "VERSION_ERROR")
                client_socket.close()
                return False
        else:
            self.send_message(client_socket, "VERSION_ERROR")
            client_socket.close()
            return False
        
    def get_local_ip(self):
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        return local_ip

    def get_public_ip(self):
        response = requests.get('https://api.ipify.org?format=json')
        public_ip = response.json()['ip']
        return public_ip

    def handle_client(self, client_socket, address):
        try:
            logging.info(f'New connection from {address}')
            client_socket.settimeout(1.0)
            if not self.version_check(client_socket):
                logging.warning(f'Version check failed for {address}')
                return

            login_attempts = 3
            while self.active_users.get(address) is None and not self.shutdown_event.is_set():
                command_first = self.receive_message(client_socket)
                if self.shutdown_event.is_set():
                    self.send_message(client_socket, "SERVER_SHUTDOWN")
                    break
                if not command_first:
                    break
                if command_first.startswith("LOGIN"):
                    logging.info(f'Login attempt from {address}')
                    while login_attempts > 0:
                        parts = command_first.split('|')
                        if len(parts) != 3:
                            self.send_message(client_socket, "ERROR|Định dạng đăng nhập không hợp lệ")
                            break
                        username, password = parts[1], parts[2]
                        if username == '' or password == '':
                            self.send_message(client_socket, "ERROR|Tên đăng nhập hoặc mật khẩu không được để trống")
                            break
                        if self.user_manager.verify_user(username, password):
                            self.send_message(client_socket, "SUCCESS|Đăng nhập thành công")
                            self.active_users[address] = username
                            logging.info(f'Successfully login as {username} from {address}')
                            break
                        else:
                            self.send_message(client_socket, "ERROR|Tên đăng nhập hoặc mật khẩu không đúng")
                            logging.warning(f'Login (attempt {4 - login_attempts}) failed for {username} from {address}')
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
                                logging.info(f'New user {username} registered from {address}')
                                break
                            else:
                                logging.warning(f'Failed to register new user {username} from {address}')
                                self.send_message(client_socket, "ERROR|Đăng ký thất bại")
                                break
                else:
                    self.send_message(client_socket, "ERROR|Unknown command")

            if self.shutdown_event.is_set():
                self.send_message(client_socket, "SERVER_SHUTDOWN")
                return

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

                    original_filename = filename
                    file_base, file_ext = os.path.splitext(filename)
                    counter = 1
                    while os.path.exists(os.path.join(storage_dir, filename)):
                        filename = f'{file_base} ({counter}){file_ext}'
                        counter += 1

                    if filename != original_filename:
                        # inform client that file name has been changed
                        self.send_message(client_socket, f"NEW_FILENAME|{filename}")
                    else:
                        self.send_message(client_socket, "FILENAME_OK")
                        
                    # self.send_message(client_socket, "FILENAME_OK")
                    
                    filesize_str = self.receive_message(client_socket)
                    filesize = 0
                    try:
                        filesize = int(filesize_str)
                    except ValueError:
                        self.send_message(client_socket, "ERROR|Kích thước tệp tin không hợp lệ")
                        continue

                    self.send_message(client_socket, "READY")
                    
                    checksum_msg = self.receive_message(client_socket)
                    checksum = ""
                    if checksum_msg.startswith("CHECKSUM:"):
                        checksum = checksum_msg.split(':', 1)[1]
                        self.send_message(client_socket, "CHECKSUM_OK")
                    
                    filepath = os.path.join(storage_dir, filename)
                    bytes_received = 0
                    with open(filepath, 'wb') as f:
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
                        calculated_checksum = self.generate_file_checksum(filepath)
                        print(f"Checksum: {calculated_checksum}")
                        
                        if checksum != calculated_checksum:
                            self.send_message(client_socket, "ERROR|Checksum không khớp")
                            os.remove(filepath)
                        else:
                            self.send_message(client_socket, "SUCCESS")
                            print(f"Tải lên tệp tin: {filename} thành công từ {address}")
                    else:
                        self.send_message(client_socket, "ERROR|Tải lên không hoàn thành")

                elif command.startswith("DOWNLOAD"):
                    username = self.active_users[address]
                    storage_dir = self.user_manager.get_user_storage(username)
                    parts = command.split(' ', 1)
                    if len(parts) < 2:
                        self.send_message(client_socket, "ERROR|Định dạng lệnh không hợp lệ")
                        continue
                    filename = parts[1]
                    filepath = os.path.join(storage_dir, filename)
                    if not os.path.exists(filepath):
                        self.send_message(client_socket, "FILE_NOT_FOUND")
                    else:
                        logging.info(f'File download request from {address}: {filename}')
                        filesize = os.path.getsize(filepath)
                        self.send_message(client_socket, str(filesize))
                        response = self.receive_message(client_socket)
                        if response == "READY":
                            checksum = self.generate_file_checksum(filepath)
                            self.send_message(client_socket, f"CHECKSUM:{checksum}")
                            response = self.receive_message(client_socket)
                            if response == "CHECKSUM_OK":
                                with open(filepath, 'rb') as f:
                                    while True:
                                        data = f.read(4096)
                                        if not data:
                                            break
                                        client_socket.sendall(data)
                                print(f"Gửi tệp tin: {filename} đến {address} thành công")
                                self.send_message(client_socket, "SUCCESS")
                                logging.info(f'File {filename} sent to {address}')
                            else:
                                self.send_message(client_socket, "ERROR|Client không nhận được checksum")
                        else:
                            self.send_message(client_socket, "ERROR|Không sẵn sàng nhận tệp tin")

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

        except Exception as e:
            print(f"Lỗi khi xử lý client {address}: {e}")
            logging.error(f'Error handling client {address}: {e}')
        finally:
            if address in self.active_users:
                logging.info(f'User {self.active_users[address]} disconnected from {address}')
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