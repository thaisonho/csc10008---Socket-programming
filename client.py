import tkinter as tk
from tkinter import messagebox
from client import gui, transfer

def main():
    root = tk.Tk()
    root.withdraw()  # Ẩn cửa sổ chính tạm thời

    # Khởi tạo đối tượng client
    client = transfer.FileTransferClient()

    # Tạo và hiển thị cửa sổ đăng nhập
    login_window = tk.Toplevel(root)
    gui.LoginWindow(login_window, client, lambda: show_main_gui(root, client))

    root.mainloop()

def show_main_gui(root, client):
    # Đóng cửa sổ đăng nhập
    root.deiconify()  # Hiện cửa sổ chính
    app = gui.FileTransferGUI(root, client)
    root.protocol("WM_DELETE_WINDOW", lambda: (app.client.close(), root.destroy()))
    # Hiển thị giao diện chính
    app.setup_gui()

if __name__ == "__main__":
    main()