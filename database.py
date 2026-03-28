"""
База данных для хранения пользователей и их портфелей
"""

import sqlite3
from datetime import datetime


class UserDatabase:
    """Класс для работы с базой данных пользователей"""
    
    def __init__(self, db_url='sqlite:///database.db'):
        # Извлекаем путь из URL
        if db_url.startswith('sqlite:///'):
            self.db_path = db_url.replace('sqlite:///', '')
        else:
            self.db_path = 'database.db'
        
        self.init_db()
    
    def init_db(self):
        """Инициализация базы данных"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Таблица пользователей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                risk_profile TEXT DEFAULT 'Средний'
            )
        ''')
        
        # Таблица портфелей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS portfolios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                token_address TEXT,
                token_name TEXT,
                amount REAL,
                value_ton REAL,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        
        # Таблица истории анализов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analysis_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                token_address TEXT,
                analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def register_user(self, user_id, username):
        """Регистрация нового пользователя"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR IGNORE INTO users (user_id, username)
            VALUES (?, ?)
        ''', (user_id, username))
        
        conn.commit()
        conn.close()
    
    def get_user_profile(self, user_id):
        """Получение профиля пользователя"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT user_id, username, risk_profile, created_at
            FROM users
            WHERE user_id = ?
        ''', (user_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'user_id': row[0],
                'username': row[1],
                'risk_profile': row[2],
                'created_at': row[3]
            }
        return {}
    
    def update_user_profile(self, user_id, updates):
        """Обновление профиля пользователя"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if 'risk_profile' in updates:
            cursor.execute('''
                UPDATE users
                SET risk_profile = ?
                WHERE user_id = ?
            ''', (updates['risk_profile'], user_id))
        
        conn.commit()
        conn.close()
    
    def add_to_portfolio(self, user_id, token_address, token_name, amount, value_ton):
        """Добавление токена в портфель"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO portfolios (user_id, token_address, token_name, amount, value_ton)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, token_address, token_name, amount, value_ton))
        
        conn.commit()
        conn.close()
    
    def get_user_portfolio(self, user_id):
        """Получение портфеля пользователя"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT token_address, token_name, amount, value_ton, added_at
            FROM portfolios
            WHERE user_id = ?
            ORDER BY added_at DESC
        ''', (user_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        portfolio = []
        for row in rows:
            portfolio.append({
                'token': row[1] or row[0][:8] + '...',
                'address': row[0],
                'amount': row[2],
                'value': row[3],
                'added_at': row[4]
            })
        
        return portfolio
    
    def log_analysis(self, user_id, token_address):
        """Логирование анализа токена"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO analysis_history (user_id, token_address)
            VALUES (?, ?)
        ''', (user_id, token_address))
        
        conn.commit()
        conn.close()
    
    def get_analysis_history(self, user_id, limit=10):
        """Получение истории анализов пользователя"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT token_address, analyzed_at
            FROM analysis_history
            WHERE user_id = ?
            ORDER BY analyzed_at DESC
            LIMIT ?
        ''', (user_id, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        history = []
        for row in rows:
            history.append({
                'token_address': row[0],
                'analyzed_at': row[1]
            })
        
        return history
