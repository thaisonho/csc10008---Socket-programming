import os
import socket
import hashlib

class FileTransferClient:
    def __init__(self, host='localhost', port=5000):
        self.host = host
        self.port = port
        self.socket = None
        self.BUFFER_SIZE = 4096  # Kích thước buffer để nhận dữ liệu
        self.PROTOCOL_VERSION = "1.0"


    def generate_file_checksum(self,file_path):
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
        
    def connect(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            # Gửi phiên bản giao thức
            self.send_message(f"VERSION {self.PROTOCOL_VERSION}")
            response = self.receive_message()
            if response != "VERSION_OK":
                raise Exception("Phiên bản giao thức không khớp")
            return True
        except Exception as e:
            raise Exception(f"Lỗi kết nối: {str(e)}")

    def send_message(self, message):
        try:
            message = f"{message}\n"
            self.socket.sendall(message.encode())
        except Exception as e:
            raise Exception(f"Lỗi gửi tin nhắn: {str(e)}")

    def receive_message(self):
        try:
            data = ''
            while not data.endswith('\n'):
                packet = self.socket.recv(self.BUFFER_SIZE).decode()
                if not packet:
                    break
                data += packet
            return data.strip()
        except Exception as e:
            raise Exception(f"Lỗi nhận tin nhắn: {str(e)}")

    def login(self, username, password):
        try:
            # Gửi thông tin đăng nhập
            self.send_message(f"LOGIN|{username}|{password}")
            response = self.receive_message()
            if response.startswith("SUCCESS"):
                return True
            else:
                raise Exception(response.split('|', 1)[1] if '|' in response else response)
        except Exception as e:
            raise Exception(f"Lỗi đăng nhập: {str(e)}")

    def upload_file(self, filepath, progress_callback=None):
        try:
            if not os.path.exists(filepath):
                raise Exception("Không tìm thấy tệp tin")

            filename = os.path.basename(filepath)
            filesize = os.path.getsize(filepath)

            # Gửi lệnh tải lên
            self.send_message(f"UPLOAD {filename}")
            response = self.receive_message()
            if response != "FILENAME_OK":
                raise Exception(f"Không hợp lệ tên tệp tin: {response}")

            # Gửi kích thước tệp tin
            self.send_message(str(filesize))
            response = self.receive_message()
            if response != "READY":
                raise Exception(f"Máy chủ không sẵn sàng: {response}")
            
            self.send_message("CHECKSUM:" + self.generate_file_checksum(filepath))
            response = self.receive_message()
            if response != "CHECKSUM_OK":
                raise Exception(f"Gửi checksum thất bại: {response}")

            # Gửi dữ liệu tệp tin
            sent = 0
            with open(filepath, 'rb') as f:
                while True:
                    data = f.read(self.BUFFER_SIZE)
                    if not data:
                        break
                    self.socket.sendall(data)
                    sent += len(data)
                    if progress_callback:
                        progress_callback((sent / filesize) * 100)

            # Đợi phản hồi xác nhận thành công
            response = self.receive_message()
            if response != "SUCCESS":
                raise Exception(f"Tải lên thất bại: {response}")

        except Exception as e:
            raise Exception(f"Lỗi tải lên: {str(e)}")

    def download_file(self, filename, save_path, progress_callback=None):
        try:
            self.send_message(f"DOWNLOAD {filename}")
            response = self.receive_message()
            file_size = 0

            if response == "FILE_NOT_FOUND":
                raise Exception("Không tìm thấy tệp tin trên máy chủ")
            
            try:
                file_size = int(response)
            except ValueError:
                raise Exception(f"Kích thước tệp tin không hợp lệ: {response}")

            # Gửi READY để nhận tệp tin
            self.send_message("READY")
            
            checksum_msg = self.receive_message()
            checksum = ""
            if checksum_msg.startswith("CHECKSUM:"):
                checksum = checksum_msg.split(':')[1]
                self.send_message("CHECKSUM_OK")
            else:
                raise Exception(f"Checksum không hợp lệ: {checksum_msg}")
            
            received = 0
            with open(save_path, 'wb') as f:
                while received < file_size:
                    data = self.socket.recv(min(self.BUFFER_SIZE, file_size - received))
                    if not data:
                        break
                    f.write(data)
                    received += len(data)
                    if progress_callback:
                        progress_callback((received / file_size) * 100)
                f.flush()
                os.fsync(f.fileno())
                        
            if checksum != self.generate_file_checksum(save_path):
                print("Checksum không khớp, tải xuống thất bại")
                print(f"Checksum: {checksum}")
                print(f"Checksum tính toán: {self.generate_file_checksum(save_path)}")
                raise Exception(f'''Checksum không khớp\n checksum: {checksum}\n checksum tính toán: {self.generate_file_checksum(save_path)}''')
            # Đợi phản hồi xác nhận thành công
            response = self.receive_message()
            if response != "SUCCESS":
                raise Exception(f"Tải xuống thất bại: {response}")

        except Exception as e:
            raise Exception(f"Lỗi tải xuống: {str(e)}")

    def list_files(self):
        try:
            self.send_message("LIST")
            response = self.receive_message()
            
            if response.startswith("ERROR"):
                return []
                
            files = response.split('\n')
            return [f for f in files if f]
        except Exception as e:
            raise Exception(f"Lỗi liệt kê tệp tin: {str(e)}")

    def close(self):
        try:
            if self.socket:
                self.socket.close()
        except Exception as e:
            print(f"Lỗi đóng kết nối: {e}")
