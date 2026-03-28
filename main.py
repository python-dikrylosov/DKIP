import telebot
from telebot import types
import os
from dotenv import load_dotenv
from agents import MarketAnalyzer, RiskAdvisor, PersonalTrader
from ton_integration import TonAPIWrapper
from database import UserDatabase
from config import Config

# Загрузка переменных окружения
load_dotenv()

# Инициализация конфигурации
config = Config()

# Инициализация бота
bot = telebot.TeleBot(config.TELEGRAM_BOT_TOKEN)

# Инициализация компонентов
ton_api = TonAPIWrapper(config.TON_API_KEY)
db = UserDatabase(config.DATABASE_URL)
market_analyzer = MarketAnalyzer(ton_api)
risk_advisor = RiskAdvisor(ton_api)
personal_trader = PersonalTrader(ton_api, db)

# Адрес мета-токена DKIP
DKIP_TOKEN_ADDRESS = "EQAp_Ypj8Dz3__S-MMOQf1W0hOVZ63qfCWOvLgnJy15K6rCt"

# Хранение состояния пользователей
user_states = {}


@bot.message_handler(commands=['start'])
def send_welcome(message):
    """Приветственное сообщение при команде /start"""
    user_id = message.from_user.id
    
    # Регистрация пользователя в базе данных
    db.register_user(user_id, message.from_user.username)
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("📊 Анализ рынка")
    btn2 = types.KeyboardButton("🛡 Оценка рисков")
    btn3 = types.KeyboardButton("💼 Мой портфель")
    btn4 = types.KeyboardButton("⚙️ Настройки")
    btn5 = types.KeyboardButton("🔍 Анализ токена")
    markup.add(btn1, btn2, btn3, btn4, btn5)
    
    welcome_text = f"""
🚀 Добро пожаловать в TON Token Marketplace v3!

Я ваш персональный ИИ-ассистент для торговли токенами в сети TON.

Особенности системы:
🧠 Многоагентный анализ рынка
📊 Глубокая аналитика и визуализация
🛡 Оценка рисков и выявление скамов
💼 Персонализированные рекомендации

Специальный фокус на мета-токене DKIP:
`{DKIP_TOKEN_ADDRESS}`

Выберите действие из меню ниже:
    """
    
    bot.reply_to(message, welcome_text, reply_markup=markup)


@bot.message_handler(commands=['help'])
def send_help(message):
    """Справка по командам"""
    help_text = """
📚 Доступные команды:

/start - Запустить бота
/help - Показать эту справку
/analyze <token_address> - Анализ конкретного токена
/risk <token_address> - Оценка рисков токена
/portfolio - Показать ваш портфель
/settings - Настройки профиля
/dkip - Специальный анализ токена DKIP

Кнопки меню:
📊 Анализ рынка - Общая аналитика рынка
🛡 Оценка рисков - Анализ рисков популярных токенов
💼 Мой портфель - Управление портфелем
⚙️ Настройки - Настройка профиля риска
🔍 Анализ токена - Детальный анализ по адресу
    """
    bot.reply_to(message, help_text)


@bot.message_handler(commands=['dkip'])
def analyze_dkip(message):
    """Специальный анализ мета-токена DKIP"""
    bot.reply_to(message, "🔍 Запускаю анализ мета-токена DKIP...")
    
    try:
        # Получение данных о токене
        token_data = ton_api.get_token_info(DKIP_TOKEN_ADDRESS)
        holders_data = ton_api.get_token_holders(DKIP_TOKEN_ADDRESS)
        
        # Анализ от агентов
        market_analysis = market_analyzer.analyze_token(DKIP_TOKEN_ADDRESS)
        risk_analysis = risk_advisor.assess_token(DKIP_TOKEN_ADDRESS)
        
        response_text = f"""
🪙 Мета-токен DKIP - Детальный анализ

📍 Адрес контракта: `{DKIP_TOKEN_ADDRESS}`

📊 Статистика:
• Держателей: {holders_data.get('total_holders', 'N/A')}
• Объем торгов: {token_data.get('volume_24h', 0)} TON
• Ликвидность: {token_data.get('liquidity', 0)} TON

🧠 Анализ рынка:
{market_analysis.get('summary', 'Нет данных')}

🛡 Оценка рисков:
{risk_analysis.get('summary', 'Нет данных')}

⚠️ Примечание:
DKIP - это мета-токен, цифровой эксперимент.
Нулевой объем торгов и отсутствие пулов ликвидности -
намеренная часть концепции, а не ошибка.
        """
        
        bot.reply_to(message, response_text, parse_mode="Markdown")
        
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка при анализе DKIP: {str(e)}")


@bot.message_handler(commands=['analyze'])
def analyze_token(message):
    """Анализ конкретного токена по адресу"""
    args = message.text.split()
    
    if len(args) < 2:
        bot.reply_to(message, "❌ Укажите адрес токена после команды /analyze")
        return
    
    token_address = args[1]
    bot.reply_to(message, f"🔍 Анализирую токен {token_address}...")
    
    try:
        market_analysis = market_analyzer.analyze_token(token_address)
        
        response_text = f"""
📊 Анализ токена: `{token_address}`

{market_analysis.get('full_report', 'Нет данных')}
        """
        
        bot.reply_to(message, response_text, parse_mode="Markdown")
        
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка при анализе: {str(e)}")


@bot.message_handler(commands=['risk'])
def risk_assessment(message):
    """Оценка рисков токена"""
    args = message.text.split()
    
    if len(args) < 2:
        bot.reply_to(message, "❌ Укажите адрес токена после команды /risk")
        return
    
    token_address = args[1]
    bot.reply_to(message, f"🛡 Оцениваю риски токена {token_address}...")
    
    try:
        risk_analysis = risk_advisor.assess_token(token_address)
        
        response_text = f"""
🛡 Оценка рисков: `{token_address}`

{risk_analysis.get('full_report', 'Нет данных')}
        """
        
        bot.reply_to(message, response_text, parse_mode="Markdown")
        
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка при оценке рисков: {str(e)}")


@bot.message_handler(commands=['portfolio'])
def show_portfolio(message):
    """Показать портфель пользователя"""
    user_id = message.from_user.id
    
    try:
        portfolio = personal_trader.get_portfolio(user_id)
        
        if not portfolio:
            bot.reply_to(message, "💼 Ваш портфель пуст. Начните анализ токенов!")
            return
        
        response_text = "💼 Ваш портфель:\n\n"
        for item in portfolio:
            response_text += f"• {item['token']}: {item['amount']} ({item['value']} TON)\n"
        
        bot.reply_to(message, response_text)
        
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {str(e)}")


@bot.message_handler(commands=['settings'])
def show_settings(message):
    """Показать настройки профиля"""
    user_id = message.from_user.id
    
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton("Низкий риск", callback_data="risk_low")
    btn2 = types.InlineKeyboardButton("Средний риск", callback_data="risk_medium")
    btn3 = types.InlineKeyboardButton("Высокий риск", callback_data="risk_high")
    markup.add(btn1, btn2, btn3)
    
    try:
        profile = db.get_user_profile(user_id)
        current_risk = profile.get('risk_profile', 'Не установлен')
        
        settings_text = f"""
⚙️ Настройки профиля

Ваш текущий профиль риска: {current_risk}

Выберите новый профиль риска:
        """
        
        bot.reply_to(message, settings_text, reply_markup=markup)
        
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {str(e)}")


@bot.callback_query_handler(func=lambda call: call.data.startswith('risk_'))
def set_risk_profile(call):
    """Установка профиля риска"""
    user_id = call.from_user.id
    risk_level = call.data.split('_')[1]
    
    risk_map = {
        'low': 'Низкий',
        'medium': 'Средний',
        'high': 'Высокий'
    }
    
    try:
        db.update_user_profile(user_id, {'risk_profile': risk_map[risk_level]})
        bot.answer_callback_query(call.id, f"✅ Профиль риска установлен: {risk_map[risk_level]}")
        
        bot.edit_message_text(
            f"✅ Ваш профиль риска обновлен: {risk_map[risk_level]}",
            call.message.chat.id,
            call.message.message_id
        )
        
    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ Ошибка: {str(e)}")


@bot.message_handler(func=lambda message: message.text == "📊 Анализ рынка")
def market_analysis_handler(message):
    """Обработчик кнопки анализа рынка"""
    bot.reply_to(message, "🔄 Запускаю анализ рынка TON...")
    
    try:
        market_overview = market_analyzer.get_market_overview()
        
        response_text = f"""
📊 Обзор рынка TON

{market_overview.get('summary', 'Нет данных')}

Топ токенов по объему:
{market_overview.get('top_tokens', 'Нет данных')}
        """
        
        bot.reply_to(message, response_text)
        
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {str(e)}")


@bot.message_handler(func=lambda message: message.text == "🛡 Оценка рисков")
def risk_assessment_handler(message):
    """Обработчик кнопки оценки рисков"""
    bot.reply_to(message, "🛡 Анализирую риски популярных токенов...")
    
    try:
        risk_overview = risk_advisor.get_market_risks()
        
        response_text = f"""
🛡 Обзор рисков рынка

{risk_overview.get('summary', 'Нет данных')}

Предупреждения:
{risk_overview.get('warnings', 'Нет предупреждений')}
        """
        
        bot.reply_to(message, response_text)
        
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {str(e)}")


@bot.message_handler(func=lambda message: message.text == "💼 Мой портфель")
def portfolio_handler(message):
    """Обработчик кнопки портфеля"""
    show_portfolio(message)


@bot.message_handler(func=lambda message: message.text == "⚙️ Настройки")
def settings_handler(message):
    """Обработчик кнопки настроек"""
    show_settings(message)


@bot.message_handler(func=lambda message: message.text == "🔍 Анализ токена")
def ask_token_address(message):
    """Запрос адреса токена для анализа"""
    user_states[message.from_user.id] = 'waiting_for_token'
    bot.reply_to(message, "🔍 Введите адрес токена для анализа:")


@bot.message_handler(func=lambda message: user_states.get(message.from_user.id) == 'waiting_for_token')
def process_token_address(message):
    """Обработка введенного адреса токена"""
    token_address = message.text.strip()
    user_states[message.from_user.id] = None
    
    bot.reply_to(message, f"🔍 Анализирую токен {token_address}...")
    
    try:
        market_analysis = market_analyzer.analyze_token(token_address)
        risk_analysis = risk_advisor.assess_token(token_address)
        
        response_text = f"""
🔍 Полный анализ токена: `{token_address}`

📊 Рыночный анализ:
{market_analysis.get('summary', 'Нет данных')}

🛡 Оценка рисков:
{risk_analysis.get('summary', 'Нет данных')}

💡 Рекомендации:
{personal_trader.get_recommendation(message.from_user.id, token_address)}
        """
        
        bot.reply_to(message, response_text, parse_mode="Markdown")
        
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка при анализе: {str(e)}")


@bot.message_handler(func=lambda message: True)
def default_handler(message):
    """Обработчик всех остальных сообщений"""
    bot.reply_to(message, "❓ Я не понял команду. Используйте /help для списка доступных команд.")


if __name__ == "__main__":
    print("🚀 TON Token Marketplace v3 запущен...")
    bot.infinity_polling()
