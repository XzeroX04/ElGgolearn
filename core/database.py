import os
import sqlite3
import json

class DatabaseManager:
    def __init__(self):
        base_dir = os.path.join(os.path.expanduser("~"), "Downloads", "ElGgolearn")
        os.makedirs(base_dir, exist_ok=True)
        self.db_path = os.path.join(base_dir, "elgolearn_data.db")
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # جدول المسارات (Roadmaps)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS roadmaps (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    topic TEXT NOT NULL,
                    level TEXT NOT NULL,
                    lang TEXT NOT NULL,
                    json_data TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            # جدول المكتبة (فيديوهات وكتب)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS library (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    type TEXT NOT NULL, -- 'video' أو 'pdf'
                    title TEXT,
                    link TEXT UNIQUE,
                    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()

    def save_roadmap(self, topic: str, level: str, lang: str, roadmap_data: dict) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO roadmaps (topic, level, lang, json_data)
                VALUES (?, ?, ?, ?)
            ''', (topic, level, lang, json.dumps(roadmap_data, ensure_ascii=False)))
            conn.commit()
            return cursor.lastrowid

    def log_library(self, title: str, link: str, item_type: str):
        """تسجيل المراجع (فيديو أو كتاب)"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO library (type, title, link)
                VALUES (?, ?, ?)
                ON CONFLICT(link) DO UPDATE SET last_accessed = CURRENT_TIMESTAMP
            ''', (item_type, title, link))
            conn.commit()

    def get_library_by_type(self, item_type: str) -> list:
        """جلب نوع محدد (video أو pdf) لعرضه في صفحته الخاصة"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT title, link FROM library WHERE type = ? ORDER BY last_accessed DESC', (item_type,))
            return [{"title": r[0], "link": r[1]} for r in cursor.fetchall()]

    def get_all_roadmaps(self) -> list:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, topic, level, created_at FROM roadmaps ORDER BY created_at DESC')
            return [{"id": r[0], "topic": r[1], "level": r[2], "date": r[3]} for r in cursor.fetchall()]

    def get_roadmap_by_id(self, roadmap_id: int) -> dict | None:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT json_data FROM roadmaps WHERE id = ?', (roadmap_id,))
            row = cursor.fetchone()
            return json.loads(row[0]) if row else None