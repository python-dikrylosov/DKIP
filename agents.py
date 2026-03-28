"""
Агенты многоагентной системы ИИ для анализа токенов TON
"""

class MarketAnalyzer:
    """Агент анализа рынка - анализирует рынок, распределение держателей и историю цены"""
    
    def __init__(self, ton_api):
        self.ton_api = ton_api
    
    def analyze_token(self, token_address):
        """Анализ конкретного токена"""
        try:
            token_info = self.ton_api.get_token_info(token_address)
            holders = self.ton_api.get_token_holders(token_address)
            price_history = self.ton_api.get_price_history(token_address)
            
            # Анализ распределения держателей
            total_holders = holders.get('total_holders', 0)
            top_holders = holders.get('top_holders', [])
            concentration = sum(h.get('percentage', 0) for h in top_holders[:5]) if top_holders else 0
            
            # Анализ объема и ликвидности
            volume_24h = token_info.get('volume_24h', 0)
            liquidity = token_info.get('liquidity', 0)
            
            # Формирование отчета
            report = {
                'summary': f"Токен имеет {total_holders} держателей. "
                          f"Концентрация у топ-5: {concentration:.1f}%. "
                          f"Объем за 24ч: {volume_24h} TON. "
                          f"Ликвидность: {liquidity} TON.",
                'full_report': f"""
📊 Детальный рыночный анализ:

• Держателей: {total_holders}
• Концентрация (топ-5): {concentration:.1f}%
• Объем торгов (24ч): {volume_24h} TON
• Ликвидность: {liquidity} TON
• Цена: {token_info.get('price', 0)} TON
• Изменение цены (24ч): {token_info.get('price_change_24h', 0)}%

💡 Выводы:
{'⚠️ Высокая концентрация держателей!' if concentration > 80 else '✅ Распределение держателей нормальное'}
{'⚠️ Низкая ликвидность!' if liquidity < 1000 else '✅ Ликвидность достаточная'}
{'✅ Активные торги' if volume_24h > 0 else '⚠️ Торгов нет'}
                """,
                'metrics': {
                    'holders': total_holders,
                    'concentration': concentration,
                    'volume_24h': volume_24h,
                    'liquidity': liquidity
                }
            }
            
            return report
            
        except Exception as e:
            return {
                'summary': f"Ошибка анализа: {str(e)}",
                'full_report': f"Ошибка при получении данных: {str(e)}"
            }
    
    def get_market_overview(self):
        """Общий обзор рынка TON"""
        try:
            # Получение данных о рынке
            market_data = self.ton_api.get_market_data()
            
            overview = {
                'summary': f"Всего токенов: {market_data.get('total_tokens', 0)}. "
                          f"Активных за 24ч: {market_data.get('active_24h', 0)}.",
                'top_tokens': market_data.get('top_tokens_by_volume', [])
            }
            
            return overview
            
        except Exception as e:
            return {
                'summary': f"Ошибка получения обзора рынка: {str(e)}",
                'top_tokens': []
            }


class RiskAdvisor:
    """Агент оценки рисков - оценивает риски токена и выявляет потенциальные скамы"""
    
    def __init__(self, ton_api):
        self.ton_api = ton_api
    
    def assess_token(self, token_address):
        """Оценка рисков конкретного токена"""
        try:
            token_info = self.ton_api.get_token_info(token_address)
            holders = self.ton_api.get_token_holders(token_address)
            
            # Расчет факторов риска
            risk_score = 0
            warnings = []
            
            # Фактор 1: Концентрация держателей
            top_holders = holders.get('top_holders', [])
            concentration = sum(h.get('percentage', 0) for h in top_holders[:5]) if top_holders else 0
            if concentration > 90:
                risk_score += 30
                warnings.append("⚠️ Экстремальная концентрация (>90%)")
            elif concentration > 80:
                risk_score += 20
                warnings.append("⚠️ Высокая концентрация (>80%)")
            
            # Фактор 2: Ликвидность
            liquidity = token_info.get('liquidity', 0)
            if liquidity == 0:
                risk_score += 25
                warnings.append("⚠️ Полное отсутствие ликвидности")
            elif liquidity < 1000:
                risk_score += 15
                warnings.append("⚠️ Очень низкая ликвидность")
            
            # Фактор 3: Объем торгов
            volume_24h = token_info.get('volume_24h', 0)
            if volume_24h == 0:
                risk_score += 20
                warnings.append("⚠️ Нет торговых операций")
            
            # Фактор 4: Количество держателей
            total_holders = holders.get('total_holders', 0)
            if total_holders < 10:
                risk_score += 15
                warnings.append("⚠️ Очень мало держателей")
            elif total_holders < 100:
                risk_score += 10
                warnings.append("⚠️ Мало держателей")
            
            # Определение уровня риска
            if risk_score >= 70:
                risk_level = "КРИТИЧЕСКИЙ"
                recommendation = "Не рекомендуется к инвестированию"
            elif risk_score >= 50:
                risk_level = "ВЫСОКИЙ"
                recommendation = "Высокий риск, требуется осторожность"
            elif risk_score >= 30:
                risk_level = "СРЕДНИЙ"
                recommendation = "Умеренный риск, диверсифицируйте"
            else:
                risk_level = "НИЗКИЙ"
                recommendation = "Относительно безопасен"
            
            report = {
                'summary': f"Уровень риска: {risk_level} ({risk_score}/100). {recommendation}",
                'full_report': f"""
🛡 Оценка рисков токена:

📈 Score риска: {risk_score}/100
🎯 Уровень: {risk_level}

⚠️ Предупреждения:
{chr(10).join(warnings) if warnings else '✅ Нет критических предупреждений'}

💡 Рекомендация:
{recommendation}

📊 Факторы:
• Концентрация: {concentration:.1f}%
• Ликвидность: {liquidity} TON
• Объем (24ч): {volume_24h} TON
• Держателей: {total_holders}
                """,
                'risk_score': risk_score,
                'risk_level': risk_level,
                'warnings': warnings
            }
            
            return report
            
        except Exception as e:
            return {
                'summary': f"Ошибка оценки рисков: {str(e)}",
                'full_report': f"Ошибка при анализе: {str(e)}"
            }
    
    def get_market_risks(self):
        """Обзор рисков по рынку"""
        try:
            market_risks = self.ton_api.get_market_risks()
            
            overview = {
                'summary': f"Средний риск на рынке: {market_risks.get('average_risk', 'N/A')}",
                'warnings': market_risks.get('general_warnings', [])
            }
            
            return overview
            
        except Exception as e:
            return {
                'summary': f"Ошибка получения обзора рисков: {str(e)}",
                'warnings': []
            }


class PersonalTrader:
    """Персональный трейдер - предоставляет персонализированные рекомендации"""
    
    def __init__(self, ton_api, database):
        self.ton_api = ton_api
        self.db = database
    
    def get_portfolio(self, user_id):
        """Получение портфеля пользователя"""
        try:
            portfolio = self.db.get_user_portfolio(user_id)
            return portfolio
        except Exception as e:
            return []
    
    def get_recommendation(self, user_id, token_address):
        """Персонализированная рекомендация по токену"""
        try:
            # Получение профиля пользователя
            profile = self.db.get_user_profile(user_id)
            risk_profile = profile.get('risk_profile', 'Средний')
            
            # Анализ токена
            risk_analysis = self.assess_token(token_address)
            risk_score = risk_analysis.get('risk_score', 50)
            
            # Генерация рекомендации на основе профиля
            if risk_profile == 'Низкий':
                if risk_score < 30:
                    return "✅ Подходит для консервативного портфеля"
                else:
                    return "⚠️ Слишком высокий риск для вашего профиля"
            
            elif risk_profile == 'Средний':
                if risk_score < 50:
                    return "✅ Подходит для умеренного портфеля"
                else:
                    return "⚠️ Рассмотрите меньшую позицию"
            
            elif risk_profile == 'Высокий':
                if risk_score < 70:
                    return "✅ Может подойти для агрессивной стратегии"
                else:
                    return "⚠️ Даже для вас это слишком рискованно"
            
            return "💡 Настройте профиль риска в настройках"
            
        except Exception as e:
            return f"Ошибка рекомендации: {str(e)}"
    
    def assess_token(self, token_address):
        """Внутренняя оценка токена (делегирование RiskAdvisor)"""
        risk_advisor = RiskAdvisor(self.ton_api)
        return risk_advisor.assess_token(token_address)
