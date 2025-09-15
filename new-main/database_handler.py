import sqlite3
import os
from datetime import datetime

class DatabaseManager:
    def __init__(self, db_path):
        # Создаем абсолютный путь к файлу базы данных
        # Предполагаем, что скрипт запускается из папки new-main
        base_dir = os.path.abspath(os.path.dirname(__file__))
        full_db_path = os.path.join(base_dir, db_path)
        
        # Убедимся, что папка существует
        os.makedirs(os.path.dirname(full_db_path), exist_ok=True)
        
        # Подключаемся к базе данных
        self.conn = sqlite3.connect(full_db_path, check_same_thread=False)
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.create_table()
        print(f"База данных создана по пути: {full_db_path}")
    
    def create_table(self):
        """Создает таблицу для хранения заявок"""
        query = """
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            phone TEXT NOT NULL,
            service_type TEXT NOT NULL,
            other_service TEXT,
            submission_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            notified BOOLEAN DEFAULT 0
        )
        """
        self.conn.execute(query)
        self.conn.commit()
        print("Таблица applications создана или уже существует")
    
    def add_application(self, first_name, last_name, phone, service_type, other_service=None):
        """Добавляет новую заявку в базу данных"""
        query = """
        INSERT INTO applications (first_name, last_name, phone, service_type, other_service)
        VALUES (?, ?, ?, ?, ?)
        """
        try:
            self.conn.execute(query, (first_name, last_name, phone, service_type, other_service))
            self.conn.commit()
            print(f"Заявка добавлена: {first_name} {last_name}, {phone}, {service_type}")
            return True
        except Exception as e:
            print(f"Ошибка при добавлении заявки: {e}")
            return False
    
    def get_applications(self):
        """Получает все заявки из базы данных"""
        query = "SELECT * FROM applications ORDER BY submission_date DESC"
        cursor = self.conn.execute(query)
        return cursor.fetchall()
    
    def get_unnotified_applications(self):
        """Получает все непрочитанные заявки"""
        query = "SELECT * FROM applications WHERE notified = 0 ORDER BY submission_date DESC"
        cursor = self.conn.execute(query)
        return cursor.fetchall()
    
    def mark_as_notified(self, application_id):
        """Помечает заявку как отправленную"""
        query = "UPDATE applications SET notified = 1 WHERE id = ?"
        self.conn.execute(query, (application_id,))
        self.conn.commit()
        print(f"Заявка #{application_id} помечена как отправленная")
    
    def close(self):
        """Закрывает соединение с базой данных"""
        self.conn.close()
        print("Соединение с базой данных закрыто")

# Создаем глобальный экземпляр DatabaseManager
db_path = os.path.join('test', 'db', 'applications.db')
db_manager = DatabaseManager(db_path)