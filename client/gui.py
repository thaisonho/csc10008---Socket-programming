# client/gui.py
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os
from datetime import datetime
from . import transfer

class LoginWindow:
    def __init__(self, master, client, on_success):
        self.master = master
        self.client = client
        self.on_success = on_success
        self.client.set_shutdown_callback(self.handle_server_shutdown)
        self.master.title("Đăng Nhập")
        self.center_window(300, 150)  # Trung tâm hóa cửa sổ với kích thước 300x150

        self.setup_gui()

    def center_window(self, width, height):
        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.master.geometry(f"{width}x{height}+{x}+{y}")
    def handle_server_shutdown(self):
        def show_shutdown_message():
            messagebox.showwarning("Thông Báo", "Server đã ngắt kết nối")
            self.master.quit()
        
        self.master.after(0, show_shutdown_message)

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
        login_button.grid(row=2, column=0, padx=5, pady=10)

        signup_button = ttk.Button(frame, text="Tạo Tài Khoản", command=self.attempt_signup)
        signup_button.grid(row=2, column=1, padx=5, pady=10)

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

    def attempt_signup(self):
        username = self.username_entry.get()
        password = self.password_entry.get()

        def signup_thread():
            try:
                if self.client.signup(username, password):
                    messagebox.showinfo("Thành công", "Tạo tài khoản thành công. Bạn có thể đăng nhập ngay bây giờ.")
                else:
                    messagebox.showerror("Lỗi", "Đăng ký thất bại")
            except Exception as e:
                messagebox.showerror("Lỗi Đăng Ký", str(e))

        threading.Thread(target=signup_thread, daemon=True).start()

class FileTransferGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Client Chuyển Tệp Tin")
        self.root.geometry("800x600")
        
        self.client = transfer.FileTransferClient()
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
        # try:
        #     self.client.connect()
        #     self.status_var.set(f"Đã kết nối tới {self.client.host}:{self.client.port}")
        #     self.open_login_window()
        # except Exception as e:
        #     messagebox.showerror("Lỗi Kết Nối", str(e))
        #     self.root.quit()
        try:
            self.client = transfer.FileTransferClient()
            # Set callback before opening login window
            self.client.set_shutdown_callback(LoginWindow.handle_server_shutdown)
            self.client.connect()
            self.open_login_window()
        except Exception as e:
            messagebox.showerror("Lỗi", str(e))

    def open_login_window(self):
        login_window = tk.Toplevel(self.root)
        login_window.grab_set()
        LoginWindow(login_window, self.client, self.show_main_gui)

    def show_main_gui(self):
        self.root.deiconify()  # Hiện cửa sổ chính sau khi đăng nhập thành công
        self.refresh_files()

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