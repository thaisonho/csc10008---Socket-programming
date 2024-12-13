import socket
import os
import sys

HOST = '169.254.5.254'  # Thay bằng địa chỉ IP của server nếu cần
PORT = 5000  # Thay bằng cổng của server nếu cần
BUFFER_SIZE = 4096
PROTOCOL_VERSION = "1.0"

def progress_bar(current, total):
    percent = 100 * current / total
    print(f"\rTiến độ: {percent:.2f}%", end='')

def send_message(client_socket, message):
    try:
        message = f"{message}\n"
        client_socket.sendall(message.encode())
    except Exception as e:
        print(f"Lỗi gửi tin nhắn: {e}")
        return False
    return True

def receive_message(client_socket):
    try:
        data = ''
        while not data.endswith('\n'):
            packet = client_socket.recv(BUFFER_SIZE).decode()
            if not packet:
                break
            data += packet
        return data.strip()
    except Exception as e:
        print(f"Lỗi nhận tin nhắn: {e}")
        return None


def send_file(client_socket, filepath):
    if not os.path.exists(filepath):
        print("File không tồn tại.")
        return
    filename = os.path.basename(filepath)
    filesize = os.path.getsize(filepath)
    try:
        if not send_message(client_socket, f"UPLOAD {filename}"):
            return
        server_response = receive_message(client_socket)
        if server_response != "FILENAME_OK":
            print(f"Server từ chối nhận file: {server_response}")
            return

        if not send_message(client_socket, str(filesize)):
            return
        server_response = receive_message(client_socket)
        if server_response != "READY":
            print(f"Server không sẵn sàng: {server_response}")
            return

        with open(filepath, 'rb') as f:
            bytes_sent = 0
            while bytes_sent < filesize:
                data = f.read(BUFFER_SIZE)
                if not data:
                    break
                client_socket.sendall(data)
                bytes_sent += len(data)
                progress_bar(bytes_sent, filesize)
        print("\nUpload hoàn tất.")
        result = receive_message(client_socket)
        if result != "SUCCESS":
            print(f"Lỗi tải lên: {result}")
        else:
            print("Tải lên thành công.")
    except Exception as e:
        print(f"Lỗi khi upload: {e}")


def receive_file(client_socket, filename):
    try:
        if not send_message(client_socket, f"DOWNLOAD {filename}"):
            return
        server_response = receive_message(client_socket)
        if server_response == "FILE_NOT_FOUND":
            print("File không tồn tại trên server.")
            return

        try:
            filesize = int(server_response)
        except ValueError:
            print(f"Kích thước file không hợp lệ: {server_response}")
            return

        if not send_message(client_socket, "READY"):
            return

        with open(filename, 'wb') as f:
            bytes_received = 0
            while bytes_received < filesize:
                data = client_socket.recv(BUFFER_SIZE)
                if not data:
                    break
                f.write(data)
                bytes_received += len(data)
                progress_bar(bytes_received, filesize)
        print("\nDownload hoàn tất.")
        result = receive_message(client_socket)
        if result != "SUCCESS":
            print(f"Lỗi tải xuống: {result}")
        else:
            print("Tải xuống thành công.")
    except Exception as e:
        print(f"Lỗi khi download: {e}")

def login(client_socket):
    username = input("Tên đăng nhập: ").strip()
    password = input("Mật khẩu: ").strip()
    if not send_message(client_socket, f"LOGIN|{username}|{password}"):
        return False
    response = receive_message(client_socket)
    if response.startswith("SUCCESS"):
        print("Đăng nhập thành công.")
        return True
    else:
        print(f"Đăng nhập thất bại: {response}")
        return False

def signup(client_socket):
    username = input("Tên đăng ký: ").strip()
    password = input("Mật khẩu: ").strip()
    if not send_message(client_socket, f"SIGNUP|{username}|{password}"):
        return False
    response = receive_message(client_socket)
    if response.startswith("SUCCESS"):
        print("Tạo tài khoản thành công.")
        return True
    else:
        print(f"Đăng ký thất bại: {response}")
        return False

def version_check(client_socket):
    if not send_message(client_socket, f"VERSION {PROTOCOL_VERSION}"):
        return False
    response = receive_message(client_socket)
    if response != "VERSION_OK":
        print(f"Lỗi phiên bản giao thức: {response}")
        return False
    return True

def main():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client_socket.connect((HOST, PORT))
    except Exception as e:
        print(f"Không thể kết nối đến server: {e}")
        sys.exit()
    print("Kết nối đến server thành công.")

    try:
        if not version_check(client_socket):
            client_socket.close()
            return

        while True:
            action = input("Bạn muốn (login/signup)? ").strip().lower()
            if action == 'login':
                 if login(client_socket):
                    break
            elif action == 'signup':
                if signup(client_socket):
                    print("Bạn có thể đăng nhập ngay bây giờ.")
            else:
                print("Lựa chọn không hợp lệ. Vui lòng chọn 'login' hoặc 'signup'.")
        
        while True:
            command = input("Nhập lệnh (upload <file>/download <file>/exit): ").strip()
            if command.startswith("upload "):
                filepath = command[7:].strip()
                send_file(client_socket, filepath)
            elif command.startswith("download "):
                filename = command[9:].strip()
                receive_file(client_socket, filename)
            elif command == "exit":
                send_message(client_socket, "EXIT")
                print("Đóng kết nối.")
                break
            else:
                print("Lệnh không hợp lệ.")
    except Exception as e:
        print(f"Lỗi: {e}")
    finally:
        client_socket.close()

if __name__ == "__main__":
    main()