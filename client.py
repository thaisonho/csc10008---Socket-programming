# client.py
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import socket
import os
import threading
from datetime import datetime
from client import gui

def main():
    root = tk.Tk()
    root.withdraw()  # Ẩn cửa sổ chính tạm thời
    app = gui.FileTransferGUI(root)
    root.after(0, app.connect_and_login)
    root.protocol("WM_DELETE_WINDOW", lambda: (app.client.close(), root.destroy()))
    root.deiconify()  # Hiện cửa sổ chính sau khi thiết lập
    root.mainloop()

if __name__ == "__main__":
    main()