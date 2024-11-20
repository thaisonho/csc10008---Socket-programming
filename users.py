import json
from pathlib import Path
import hashlib
import os

class UserManager:
    def __init__(self, users_file='users.json'):
        self.users_file = users_file
        self.users = self.load_users()
        
    def load_users(self):
        if os.path.exists(self.users_file):
            with open(self.users_file, 'r') as f:
                self.users = json.load(f)
        else:
            self.users = {}
        return self.users
        
    def _save_users(self):
        with open(self.users_file, 'w') as f:
            json.dump(self.users, f, indent=4)
            
    def _hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()
        
    def add_user(self, username, password, storage_dir=None):
        if username in self.users:
            return False  # Người dùng đã tồn tại
        if storage_dir is None:
            storage_dir = os.path.join('user_storage', username)
        hashed_password = self._hash_password(password)
        self.users[username] = {'password': hashed_password, 'storage_dir': storage_dir}
        self._save_users()
        os.makedirs(storage_dir, exist_ok=True)
        return True
        
    def verify_user(self, username, password):
        return username in self.users and self.users[username]['password'] == self._hash_password(password)
        
    def get_user_storage(self, username):
        if username not in self.users:
            return None
        return self.users[username]['storage_dir']