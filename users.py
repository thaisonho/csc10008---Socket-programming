import json
from pathlib import Path
import hashlib
import os

class UserManager:
    def __init__(self, users_file='users.txt'):
        self.users_file = users_file
        self.users = self.load_users()
        
    def load_users(self):
        users = {}
        if os.path.exists(self.users_file):
            with open(self.users_file, 'r') as f:
                for line in f:
                    parts = line.strip().split(':')
                    if len(parts) >= 2:
                        username = parts[0]
                        password = parts[1]
                        storage_dir = parts[2] if len(parts) == 3 else f"{username}_storage"
                        users[username] = {'password': password, 'storage_dir': storage_dir}
        return users
        
    def _save_users(self):
        with open(self.users_file, 'w') as f:
            json.dump(self.users, f, indent=4)
            
    def _hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()
        
    def add_user(self, username, password, storage_dir=None):
        if username in self.users:
            return False  # Người dùng đã tồn tại
        if storage_dir is None:
            storage_dir = f"{username}_storage"  # Tạo thư mục lưu trữ mặc định
        hashed_password = self._hash_password(password)
        self.users[username] = {'password': hashed_password, 'storage_dir': storage_dir}
        with open(self.users_file, 'a') as f:
            f.write(f"{username}:{hashed_password}:{storage_dir}\n")
        # Tạo thư mục lưu trữ cho người dùng
        os.makedirs(storage_dir, exist_ok=True)
        return True
        
    def verify_user(self, username, password):
        return username in self.users and self.users[username]['password'] == self._hash_password(password)
        
    def get_user_storage(self, username):
        if username not in self.users:
            return None
        return self.users[username]['storage_dir']