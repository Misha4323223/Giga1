import os
import requests
import json
import uuid
import time
import logging
from datetime import datetime, timedelta
from search_service import SearchService

class GigaChatModel:
    def __init__(self):
        self.api_key = os.environ.get("GIGACHAT_API_KEY")
        self.access_token = None
        self.token_expires_at = None
        self.base_url = "https://gigachat.devices.sberbank.ru/api/v1"
        
        # Инициализируем сервис поиска
        self.search_service = SearchService()
        
        if not self.api_key:
            logging.error("GIGACHAT_API_KEY не найден в переменных окружения")
            self.model_loaded = False
        else:
            logging.info("Инициализация GigaChat...")
            self.model_loaded = True
            self._get_access_token()
    
    def _get_access_token(self):
        """Получение токена доступа для GigaChat API"""
        try:
            url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
            
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'application/json',
                'RqUID': str(uuid.uuid4()),
                'Authorization': f'Basic {self.api_key}'
            }
            
            data = {
                'scope': 'GIGACHAT_API_PERS'
            }
            
            response = requests.post(url, headers=headers, data=data, verify=False)
            
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data['access_token']
                # Токен действует 30 минут
                self.token_expires_at = datetime.now() + timedelta(minutes=25)
                logging.info("GigaChat токен получен успешно")
                return True
            else:
                logging.error(f"Ошибка получения токена: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logging.error(f"Ошибка при получении токена GigaChat: {str(e)}")
            return False
    
    def _ensure_valid_token(self):
        """Проверка и обновление токена при необходимости"""
        if not self.access_token or (self.token_expires_at and datetime.now() >= self.token_expires_at):
            return self._get_access_token()
        return True
    
    def generate_response(self, user_message, chat_history=None):
        """Генерация ответа от GigaChat с поиском в интернете"""
        if not self.model_loaded:
            return "Ошибка: GigaChat API не настроен. Проверьте API ключ."
        
        if not self._ensure_valid_token():
            return "Ошибка авторизации в GigaChat. Проверьте API ключ."
        
        # Проверяем, нужен ли поиск в интернете
        search_result = None
        if self.search_service.should_search(user_message):
            logging.info(f"Выполняется поиск в интернете для: {user_message}")
            search_result = self.search_service.search(user_message)
        
        try:
            # Подготавливаем сообщения для API
            messages = self._prepare_messages(user_message, chat_history, search_result)
            
            url = f"{self.base_url}/chat/completions"
            
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'Authorization': f'Bearer {self.access_token}'
            }
            
            payload = {
                "model": "GigaChat",
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 512,
                "n": 1,
                "stream": False,
                "update_interval": 0
            }
            
            response = requests.post(url, headers=headers, json=payload, verify=False)
            
            if response.status_code == 200:
                result = response.json()
                if 'choices' in result and len(result['choices']) > 0:
                    ai_response = result['choices'][0]['message']['content'].strip()
                    
                    # Если был поиск, источники уже включены в ответ ИИ
                    return ai_response
                else:
                    return "Не удалось получить ответ от GigaChat."
            else:
                logging.error(f"Ошибка GigaChat API: {response.status_code} - {response.text}")
                return f"Ошибка API GigaChat: {response.status_code}"
                
        except Exception as e:
            logging.error(f"Ошибка при обращении к GigaChat: {str(e)}")
            return "Произошла ошибка при генерации ответа. Попробуйте еще раз."
    
    def _prepare_messages(self, user_message, chat_history=None, search_result=None):
        """Подготовка сообщений для GigaChat API"""
        messages = []
        
        # Системное сообщение с учетом поиска
        system_content = "Ты полезный AI-ассистент. Отвечай на русском языке кратко и по существу."
        if search_result:
            system_content = "Ты AI-ассистент с доступом к актуальной информации из интернета. Тебе предоставлены свежие данные из надёжных источников. ВАЖНО: Используй ТОЛЬКО предоставленную актуальную информацию для ответа. Не говори, что у тебя нет доступа к интернету - у тебя есть актуальные данные!"
        
        messages.append({
            "role": "system",
            "content": system_content
        })
        
        # Добавляем историю чата (последние 10 сообщений)
        if chat_history:
            recent_history = chat_history[-10:] if len(chat_history) > 10 else chat_history
            
            for message in recent_history:
                if message['role'] == 'user':
                    messages.append({
                        "role": "user",
                        "content": message['content']
                    })
                elif message['role'] == 'assistant':
                    messages.append({
                        "role": "assistant",
                        "content": message['content']
                    })
        
        # Формируем текущее сообщение
        current_message = user_message
        if search_result:
            current_message = f"Пользователь спрашивает: {user_message}\n\n=== АКТУАЛЬНЫЕ ДАННЫЕ ИЗ ИНТЕРНЕТА ===\n{search_result}\n\n=== ИНСТРУКЦИЯ ===\nОтветь на вопрос пользователя, используя ТОЛЬКО предоставленную выше актуальную информацию. Не упоминай ограничения доступа к интернету - у тебя есть свежие данные!"
        
        messages.append({
            "role": "user",
            "content": current_message
        })
        
        return messages
    
    def get_status(self):
        """Получение статуса модели"""
        if not self.model_loaded:
            return {
                'status': 'error',
                'message': 'API ключ не настроен'
            }
        
        if not self.access_token:
            return {
                'status': 'loading',
                'message': 'Получение токена доступа...'
            }
        
        return {
            'status': 'ready',
            'message': 'GigaChat готов к работе',
            'model': 'GigaChat API'
        }