# client.py
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import socket
import os
import threading
from datetime import datetime

class FileTransferClient:
    def __init__(self, host='localhost', port=5000):
        self.host = host
        self.port = port
        self.socket = None
        self.BUFFER_SIZE = 4096  # Kích thước buffer để nhận dữ liệu
        self.PROTOCOL_VERSION = "1.0"
        
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

            if response == "FILE_NOT_FOUND":
                raise Exception("Không tìm thấy tệp tin trên máy chủ")
            
            try:
                file_size = int(response)
            except ValueError:
                raise Exception(f"Kích thước tệp tin không hợp lệ: {response}")

            # Gửi READY để nhận tệp tin
            self.send_message("READY")

            received = 0
            with open(save_path, 'wb') as f:
                while received < file_size:
                    data = self.socket.recv(self.BUFFER_SIZE)
                    if not data:
                        break
                    f.write(data)
                    received += len(data)
                    if progress_callback:
                        progress_callback((received / file_size) * 100)

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

class LoginWindow:
    def __init__(self, master, client, on_success):
        self.master = master
        self.client = client
        self.on_success = on_success

        self.master.title("Đăng Nhập")
        self.master.geometry("300x150")

        self.setup_gui()

    def setup_gui(self):
        frame = ttk.Frame(self.master, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Tên đăng nhập:").grid(row=0, column=0, pady=5, sticky=tk.W)
        self.username_entry = ttk.Entry(frame)
        self.username_entry.grid(row=0, column=1, pady=5)

        ttk.Label(frame, text="Mật khẩu:").grid(row=1, column=0, pady=5, sticky=tk.W)
        self.password_entry = ttk.Entry(frame, show="*")
        self.password_entry.grid(row=1, column=1, pady=5)

        login_button = ttk.Button(frame, text="Đăng Nhập", command=self.attempt_login)
        login_button.grid(row=2, column=0, columnspan=2, pady=10)

    def attempt_login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()

        def login_thread():
            try:
                if self.client.login(username, password):
                    messagebox.showinfo("Thành công", "Đăng nhập thành công")
                    self.master.destroy()
                    self.on_success()
            except Exception as e:
                messagebox.showerror("Lỗi Đăng Nhập", str(e))

        threading.Thread(target=login_thread, daemon=True).start()

class FileTransferGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Client Chuyển Tệp Tin")
        self.root.geometry("800x600")
        
        self.client = FileTransferClient()
        self.setup_gui()

    def setup_gui(self):
        # Frame chính
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Frame chứa các nút
        btn_frame = ttk.Frame(self.main_frame)
        btn_frame.pack(fill=tk.X, pady=(0, 10))
        
        upload_btn = ttk.Button(btn_frame, text="Tải Lên", command=self.upload_file)
        upload_btn.pack(side=tk.LEFT, padx=5)
        
        download_btn = ttk.Button(btn_frame, text="Tải Xuống", command=self.download_selected)
        download_btn.pack(side=tk.LEFT, padx=5)
        
        refresh_btn = ttk.Button(btn_frame, text="Làm Mới", command=self.refresh_files)
        refresh_btn.pack(side=tk.LEFT, padx=5)

        # Thanh tiến trình
        self.progress_var = tk.DoubleVar()
        self.progress = ttk.Progressbar(self.main_frame, variable=self.progress_var, maximum=100)
        self.progress.pack(fill=tk.X, pady=5)

        # Danh sách tệp tin
        columns = ('name', 'size', 'date')
        self.tree = ttk.Treeview(self.main_frame, columns=columns, show='headings')
        
        self.tree.heading('name', text='Tên Tệp Tin')
        self.tree.heading('size', text='Kích Thước')
        self.tree.heading('date', text='Ngày Sửa Đổi')
        
        self.tree.column('name', width=400)
        self.tree.column('size', width=100, anchor='center')
        self.tree.column('date', width=200, anchor='center')

        # Thanh cuộn
        scrollbar = ttk.Scrollbar(self.main_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        scrollbar.pack(fill=tk.Y, side=tk.RIGHT)

        # Thanh trạng thái
        self.status_var = tk.StringVar(value="Chưa kết nối")
        ttk.Label(self.main_frame, textvariable=self.status_var).pack(fill=tk.X, pady=(5, 0))

    def connect_and_login(self):
        try:
            self.client.connect()
            self.status_var.set(f"Đã kết nối tới {self.client.host}:{self.client.port}")
            self.open_login_window()
        except Exception as e:
            messagebox.showerror("Lỗi Kết Nối", str(e))
            self.root.quit()

    def open_login_window(self):
        login_window = tk.Toplevel(self.root)
        login_window.grab_set()
        LoginWindow(login_window, self.client, self.show_main_gui)

    def show_main_gui(self):
        self.refresh_files()

    def format_size(self, size):
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} PB"

    def upload_file(self):
        filepath = filedialog.askopenfilename()
        if filepath:
            def upload():
                try:
                    self.status_var.set("Đang tải lên...")
                    self.client.upload_file(filepath, self.update_progress)
                    self.status_var.set("Tải lên thành công")
                    self.refresh_files()
                except Exception as e:
                    messagebox.showerror("Lỗi Tải Lên", str(e))
                finally:
                    self.progress_var.set(0)
            
            threading.Thread(target=upload, daemon=True).start()

    def download_selected(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Cần Chọn Tệp Tin", "Vui lòng chọn một tệp tin để tải xuống")
            return

        filename = self.tree.item(selection[0])['values'][0]
        save_path = filedialog.asksaveasfilename(defaultextension="", initialfile=filename)
        
        if save_path:
            def download():
                try:
                    self.status_var.set("Đang tải xuống...")
                    self.client.download_file(filename, save_path, self.update_progress)
                    self.status_var.set("Tải xuống thành công")
                except Exception as e:
                    messagebox.showerror("Lỗi Tải Xuống", str(e))
                finally:
                    self.progress_var.set(0)
            
            threading.Thread(target=download, daemon=True).start()

    def refresh_files(self):
        try:
            files = self.client.list_files()
            for item in self.tree.get_children():
                self.tree.delete(item)
            for file_info in files:
                # Giả sử máy chủ gửi "filename|size"
                if '|' in file_info:
                    name, size = file_info.split('|', 1)
                    size = self.format_size(int(size))
                    date = datetime.now().strftime("%Y-%m-%d %H:%M")
                    self.tree.insert('', tk.END, values=(name, size, date))
                else:
                    name = file_info
                    size = "-"
                    date = "-"
                    self.tree.insert('', tk.END, values=(name, size, date))
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể làm mới danh sách tệp tin: {str(e)}")

    def update_progress(self, value):
        self.progress_var.set(value)

def main():
    root = tk.Tk()
    root.withdraw()  # Ẩn cửa sổ chính tạm thời
    app = FileTransferGUI(root)
    root.after(0, app.connect_and_login)
    root.protocol("WM_DELETE_WINDOW", lambda: (app.client.close(), root.destroy()))
    root.deiconify()  # Hiện cửa sổ chính sau khi thiết lập
    root.mainloop()

if __name__ == "__main__":
    main()