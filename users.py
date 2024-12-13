import sqlite3
import hashlib
import os

class UserManager:
    def __init__(self, db_file='users.db'):
        self.db_file = db_file
        self._initialize_database()

    def _initialize_database(self):
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    storage_dir TEXT NOT NULL
                )
            """)
            conn.commit()

    def _hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def add_user(self, username, password):
        # Tự động tạo đường dẫn lưu trữ dựa trên tên người dùng
        storage_dir = os.path.join('user_storage', username)
        hashed_password = self._hash_password(password)

        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO users (username, password, storage_dir)
                    VALUES (?, ?, ?)
                """, (username, hashed_password, storage_dir))
                conn.commit()
            os.makedirs(storage_dir, exist_ok=True)
            return True
        except sqlite3.IntegrityError:
            return False  # Người dùng đã tồn tại

    def verify_user(self, username, password):
        hashed_password = self._hash_password(password)
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM users WHERE username = ? AND password = ?
            """, (username, hashed_password))
            return cursor.fetchone() is not None

    def user_exists(self, username):
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM users WHERE username = ?
            """, (username,))
            return cursor.fetchone() is not None

    def get_user_storage(self, username):
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT storage_dir FROM users WHERE username = ?
            """, (username,))
            result = cursor.fetchone()
            return result[0] if result else None
