"""
Асинхронное PyQt6 приложение для анализа токенов TON
Многоагентная ИИ система с графическим интерфейсом
"""

import sys
import asyncio
from datetime import datetime
from typing import Optional, Dict, Any

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTextEdit, QLineEdit, QTabWidget,
    QProgressBar, QStatusBar, QMenu, QMenuBar, QAction,
    QSplitter, QFrame, QScrollArea, QSizePolicy, QMessageBox,
    QDialog, QDialogButtonBox, QFormLayout, QComboBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QMetaObject
from PyQt6.QtGui import QFont, QColor, QIcon, QActionGroup

from agents import MarketAnalyzer, RiskAdvisor, PersonalTrader
from ton_integration import TonAPIWrapper
from database import UserDatabase
from config import Config


class AsyncWorker(QThread):
    """Асинхронный воркер для выполнения задач в отдельном потоке"""
    result_ready = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    progress_update = pyqtSignal(int, str)
    
    def __init__(self, task_func, *args, **kwargs):
        super().__init__()
        self.task_func = task_func
        self.args = args
        self.kwargs = kwargs
    
    def run(self):
        try:
            result = self.task_func(*self.args, **self.kwargs)
            self.result_ready.emit(result)
        except Exception as e:
            self.error_occurred.emit(str(e))


class TokenInfoCard(QFrame):
    """Карточка с информацией о токене"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        self.setStyleSheet("""
            QFrame {
                background-color: #2b2b2b;
                border-radius: 10px;
                padding: 15px;
                margin: 5px;
            }
            QLabel {
                color: #ffffff;
            }
        """)
        
        layout = QVBoxLayout(self)
        
        self.title_label = QLabel("📊 Информация о токене")
        self.title_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(self.title_label)
        
        self.content_label = QLabel("Введите адрес токена для анализа")
        self.content_label.setWordWrap(True)
        layout.addWidget(self.content_label)
    
    def update_content(self, data: Dict[str, Any]):
        """Обновление содержимого карточки"""
        content = f"""
        <style>
            .metric {{ color: #4CAF50; font-weight: bold; }}
            .warning {{ color: #FF9800; }}
            .danger {{ color: #F44336; }}
        </style>
        
        <p><b>Цена:</b> <span class="metric">{data.get('price', 'N/A')} TON</span></p>
        <p><b>Объем (24ч):</b> {data.get('volume_24h', 0)} TON</p>
        <p><b>Ликвидность:</b> {data.get('liquidity', 0)} TON</p>
        <p><b>Изменение (24ч):</b> 
            <span class="{'metric' if data.get('price_change_24h', 0) >= 0 else 'danger'}">
                {data.get('price_change_24h', 0)}%
            </span>
        </p>
        <p><b>Держателей:</b> {data.get('holders', 0)}</p>
        <p><b>Концентрация:</b> 
            <span class="{'warning' if data.get('concentration', 0) > 80 else 'metric'}">
                {data.get('concentration', 0):.1f}%
            </span>
        </p>
        """
        self.content_label.setText(content)


class RiskMeter(QFrame):
    """Индикатор риска"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        self.setStyleSheet("""
            QFrame {
                background-color: #2b2b2b;
                border-radius: 10px;
                padding: 15px;
                margin: 5px;
            }
        """)
        
        layout = QVBoxLayout(self)
        
        self.title_label = QLabel("🛡 Оценка рисков")
        self.title_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(self.title_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #444444;
                border-radius: 5px;
                text-align: center;
                color: white;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 5px;
            }
        """)
        layout.addWidget(self.progress_bar)
        
        self.risk_label = QLabel("Уровень риска: Не оценен")
        self.risk_label.setFont(QFont("Arial", 12))
        layout.addWidget(self.risk_label)
        
        self.warnings_label = QLabel("")
        self.warnings_label.setWordWrap(True)
        self.warnings_label.setStyleSheet("color: #FF9800;")
        layout.addWidget(self.warnings_label)
    
    def update_risk(self, risk_data: Dict[str, Any]):
        """Обновление индикатора риска"""
        risk_score = risk_data.get('risk_score', 0)
        risk_level = risk_data.get('risk_level', 'Неизвестно')
        warnings = risk_data.get('warnings', [])
        
        self.progress_bar.setValue(risk_score)
        
        # Цвет прогресс бара в зависимости от риска
        if risk_score < 30:
            color = "#4CAF50"  # Зеленый
        elif risk_score < 50:
            color = "#FF9800"  # Оранжевый
        else:
            color = "#F44336"  # Красный
        
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: #444444;
                border-radius: 5px;
                text-align: center;
                color: white;
            }}
            QProgressBar::chunk {{
                background-color: {color};
                border-radius: 5px;
            }}
        """)
        
        self.risk_label.setText(f"Уровень риска: {risk_level} ({risk_score}/100)")
        
        if warnings:
            self.warnings_label.setText("⚠️ " + "<br>⚠️ ".join(warnings))
        else:
            self.warnings_label.setText("✅ Нет критических предупреждений")


class RecommendationPanel(QFrame):
    """Панель рекомендаций"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        self.setStyleSheet("""
            QFrame {
                background-color: #2b2b2b;
                border-radius: 10px;
                padding: 15px;
                margin: 5px;
            }
        """)
        
        layout = QVBoxLayout(self)
        
        self.title_label = QLabel("💡 Рекомендации ИИ")
        self.title_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(self.title_label)
        
        self.recommendation_label = QLabel("Проведите анализ токена для получения рекомендаций")
        self.recommendation_label.setWordWrap(True)
        self.recommendation_label.setFont(QFont("Arial", 11))
        layout.addWidget(self.recommendation_label)
    
    def update_recommendation(self, text: str):
        """Обновление рекомендации"""
        self.recommendation_label.setText(text)


class MainWindow(QMainWindow):
    """Главное окно приложения"""
    
    def __init__(self):
        super().__init__()
        
        # Инициализация компонентов
        self.ton_api = TonAPIWrapper(Config.TON_API_KEY)
        self.database = UserDatabase(Config.DATABASE_URL)
        self.market_analyzer = MarketAnalyzer(self.ton_api)
        self.risk_advisor = RiskAdvisor(self.ton_api)
        self.personal_trader = PersonalTrader(self.ton_api, self.database)
        
        # Текущий пользователь (для демонстрации - фиксированный ID)
        self.current_user_id = 1
        self.current_token_address = ""
        
        self.init_ui()
        self.register_user()
    
    def init_ui(self):
        """Инициализация пользовательского интерфейса"""
        self.setWindowTitle(f"{Config.APP_NAME} v{Config.VERSION}")
        self.setMinimumSize(1200, 800)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
            }
        """)
        
        # Создание меню
        self.create_menu_bar()
        
        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # Заголовок
        header_layout = QHBoxLayout()
        title_label = QLabel(f"🚀 {Config.APP_NAME}")
        title_label.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #0088cc;")
        header_layout.addWidget(title_label)
        
        self.status_label = QLabel("Готов к работе")
        self.status_label.setStyleSheet("color: #888888;")
        header_layout.addWidget(self.status_label, alignment=Qt.AlignmentFlag.AlignRight)
        
        main_layout.addLayout(header_layout)
        
        # Поле ввода адреса токена
        input_layout = QHBoxLayout()
        input_layout.addWidget(QLabel("Адрес токена:"))
        
        self.token_input = QLineEdit()
        self.token_input.setPlaceholderText("Введите адрес токена TON (например, EQAp_Ypj8Dz3__S-MMOQf1W0hOVZ63qfCWOvLgnJy15K6rCt)")
        self.token_input.setMinimumHeight(40)
        self.token_input.setStyleSheet("""
            QLineEdit {
                background-color: #2b2b2b;
                color: white;
                border: 2px solid #0088cc;
                border-radius: 5px;
                padding: 10px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #00aaff;
            }
        """)
        input_layout.addWidget(self.token_input, stretch=1)
        
        self.analyze_button = QPushButton("🔍 Анализировать")
        self.analyze_button.setMinimumHeight(40)
        self.analyze_button.setMinimumWidth(150)
        self.analyze_button.setStyleSheet("""
            QPushButton {
                background-color: #0088cc;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #00aaff;
            }
            QPushButton:pressed {
                background-color: #006699;
            }
            QPushButton:disabled {
                background-color: #555555;
            }
        """)
        self.analyze_button.clicked.connect(self.start_analysis)
        input_layout.addWidget(self.analyze_button)
        
        main_layout.addLayout(input_layout)
        
        # Разделитель для панелей
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Левая панель - информация о токене
        left_panel = QScrollArea()
        left_panel.setWidgetResizable(True)
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        self.token_card = TokenInfoCard()
        left_layout.addWidget(self.token_card)
        
        self.risk_meter = RiskMeter()
        left_layout.addWidget(self.risk_meter)
        
        left_panel.setWidget(left_widget)
        splitter.addWidget(left_panel)
        
        # Правая панель - рекомендации и история
        right_panel = QScrollArea()
        right_panel.setWidgetResizable(True)
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        self.recommendation_panel = RecommendationPanel()
        right_layout.addWidget(self.recommendation_panel)
        
        # История анализов
        history_label = QLabel("📜 История анализов")
        history_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        history_label.setStyleSheet("color: white; margin-top: 20px;")
        right_layout.addWidget(history_label)
        
        self.history_text = QTextEdit()
        self.history_text.setReadOnly(True)
        self.history_text.setMinimumHeight(200)
        self.history_text.setStyleSheet("""
            QTextEdit {
                background-color: #2b2b2b;
                color: #cccccc;
                border: 1px solid #444444;
                border-radius: 5px;
                padding: 10px;
                font-family: 'Consolas', monospace;
            }
        """)
        right_layout.addWidget(self.history_text)
        
        right_panel.setWidget(right_widget)
        splitter.addWidget(right_panel)
        
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        
        main_layout.addWidget(splitter)
        
        # Статус бар
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Приложение готово")
        
        # Быстрые кнопки
        quick_buttons_layout = QHBoxLayout()
        
        self.dkip_button = QPushButton("🎯 Анализировать DKIP")
        self.dkip_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #66BB6A;
            }
        """)
        self.dkip_button.clicked.connect(self.analyze_dkip)
        quick_buttons_layout.addWidget(self.dkip_button)
        
        self.clear_button = QPushButton("🗑 Очистить")
        self.clear_button.setStyleSheet("""
            QPushButton {
                background-color: #757575;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #9E9E9E;
            }
        """)
        self.clear_button.clicked.connect(self.clear_all)
        quick_buttons_layout.addWidget(self.clear_button)
        
        main_layout.addLayout(quick_buttons_layout)
    
    def create_menu_bar(self):
        """Создание меню приложения"""
        menubar = self.menuBar()
        menubar.setStyleSheet("""
            QMenuBar {
                background-color: #1e1e1e;
                color: white;
            }
            QMenuBar::item:selected {
                background-color: #333333;
            }
            QMenu {
                background-color: #2b2b2b;
                color: white;
            }
            QMenu::item:selected {
                background-color: #0088cc;
            }
        """)
        
        # Меню Файл
        file_menu = menubar.addMenu("Файл")
        
        exit_action = QAction("Выход", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Меню Настройки
        settings_menu = menubar.addMenu("Настройки")
        
        profile_action = QAction("Профиль пользователя", self)
        profile_action.triggered.connect(self.show_profile_dialog)
        settings_menu.addAction(profile_action)
        
        # Меню Помощь
        help_menu = menubar.addMenu("Помощь")
        
        about_action = QAction("О программе", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def register_user(self):
        """Регистрация текущего пользователя"""
        self.database.register_user(self.current_user_id, "pyqt6_user")
    
    def start_analysis(self):
        """Запуск анализа токена"""
        token_address = self.token_input.text().strip()
        
        if not token_address:
            QMessageBox.warning(self, "Ошибка", "Введите адрес токена!")
            return
        
        self.current_token_address = token_address
        self.statusBar.showMessage(f"Анализ токена: {token_address[:16]}...")
        self.analyze_button.setEnabled(False)
        self.status_label.setText("Анализ выполняется...")
        
        # Запуск анализа в отдельном потоке
        self.worker = AsyncWorker(self.perform_full_analysis, token_address)
        self.worker.result_ready.connect(self.on_analysis_complete)
        self.worker.error_occurred.connect(self.on_analysis_error)
        self.worker.start()
    
    def perform_full_analysis(self, token_address: str) -> Dict[str, Any]:
        """Выполнение полного анализа токена"""
        # Анализ рынка
        market_report = self.market_analyzer.analyze_token(token_address)
        
        # Оценка рисков
        risk_report = self.risk_advisor.assess_token(token_address)
        
        # Персональная рекомендация
        recommendation = self.personal_trader.get_recommendation(
            self.current_user_id, token_address
        )
        
        # Логирование анализа
        self.database.log_analysis(self.current_user_id, token_address)
        
        return {
            'market': market_report,
            'risk': risk_report,
            'recommendation': recommendation,
            'token_address': token_address
        }
    
    def on_analysis_complete(self, result: Dict[str, Any]):
        """Обработка результатов анализа"""
        self.analyze_button.setEnabled(True)
        self.status_label.setText("Анализ завершен")
        self.statusBar.showMessage(f"Анализ завершен: {datetime.now().strftime('%H:%M:%S')}")
        
        # Обновление UI с результатами
        market_data = result['market']
        risk_data = result['risk']
        recommendation = result['recommendation']
        
        # Подготовка данных для отображения
        token_info = {
            'price': market_data.get('metrics', {}).get('price', 0),
            'volume_24h': market_data.get('metrics', {}).get('volume_24h', 0),
            'liquidity': market_data.get('metrics', {}).get('liquidity', 0),
            'price_change_24h': 0,
            'holders': market_data.get('metrics', {}).get('holders', 0),
            'concentration': market_data.get('metrics', {}).get('concentration', 0)
        }
        
        self.token_card.update_content(token_info)
        self.risk_meter.update_risk(risk_data)
        self.recommendation_panel.update_recommendation(recommendation)
        
        # Добавление в историю
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        history_entry = f"[{timestamp}] Анализ: {result['token_address'][:16]}...\n"
        history_entry += f"  Риск: {risk_data.get('risk_level', 'N/A')} ({risk_data.get('risk_score', 0)}/100)\n"
        history_entry += f"  Рекомендация: {recommendation}\n\n"
        
        self.history_text.insertPlainText(history_entry)
        self.history_text.moveCursor(self.history_text.textCursor().MoveOperation.End)
    
    def on_analysis_error(self, error_message: str):
        """Обработка ошибки анализа"""
        self.analyze_button.setEnabled(True)
        self.status_label.setText("Ошибка анализа")
        self.statusBar.showMessage(f"Ошибка: {error_message}")
        
        QMessageBox.critical(self, "Ошибка анализа", f"Произошла ошибка при анализе:\n{error_message}")
    
    def analyze_dkip(self):
        """Анализ мета-токена DKIP"""
        self.token_input.setText(Config.DKIP_TOKEN_ADDRESS)
        self.start_analysis()
    
    def clear_all(self):
        """Очистка всех данных"""
        self.token_input.clear()
        self.history_text.clear()
        self.status_label.setText("Готов к работе")
        self.statusBar.showMessage("Данные очищены")
    
    def show_profile_dialog(self):
        """Показ диалога профиля пользователя"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Профиль пользователя")
        dialog.setMinimumWidth(400)
        dialog.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
                color: white;
            }
        """)
        
        layout = QFormLayout(dialog)
        
        # Профиль риска
        risk_combo = QComboBox()
        risk_combo.addItems(["Низкий", "Средний", "Высокий"])
        
        profile = self.database.get_user_profile(self.current_user_id)
        current_risk = profile.get('risk_profile', 'Средний')
        risk_combo.setCurrentText(current_risk)
        
        layout.addRow("Профиль риска:", risk_combo)
        
        # Кнопки
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_risk = risk_combo.currentText()
            self.database.update_user_profile(
                self.current_user_id,
                {'risk_profile': new_risk}
            )
            QMessageBox.information(self, "Профиль обновлен", f"Профиль риска изменен на: {new_risk}")
    
    def show_about(self):
        """Показ окна о программе"""
        about_text = f"""
        <h2>{Config.APP_NAME}</h2>
        <p>Версия: {Config.VERSION}</p>
        <p>Разработчик: {Config.DEVELOPER}</p>
        <p>Многоагентная ИИ система для анализа токенов TON Blockchain</p>
        <p>Технологии: PyQt6, asyncio, SQLite</p>
        <hr>
        <p>© 2024 Все права защищены</p>
        """
        
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("О программе")
        msg_box.setTextFormat(Qt.TextFormat.RichText)
        msg_box.setText(about_text)
        msg_box.exec()


def main():
    """Точка входа приложения"""
    # Создание приложения
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    # Установка темной палитры
    from PyQt6.QtGui import QPalette
    from PyQt6.QtCore import QPalette
    
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(30, 30, 30))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(255, 255, 255))
    palette.setColor(QPalette.ColorRole.Base, QColor(43, 43, 43))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(68, 68, 68))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(255, 255, 255))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(255, 255, 255))
    palette.setColor(QPalette.ColorRole.Text, QColor(255, 255, 255))
    palette.setColor(QPalette.ColorRole.Button, QColor(43, 43, 43))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(255, 255, 255))
    palette.setColor(QPalette.ColorRole.BrightText, QColor(0, 136, 204))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(0, 136, 204))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
    
    app.setPalette(palette)
    
    # Создание и показ главного окна
    window = MainWindow()
    window.show()
    
    # Запуск цикла событий
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
