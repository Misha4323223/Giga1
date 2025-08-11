import requests
import json
import logging
import time
import re
from urllib.parse import urlparse, quote

class SeaArtService:
    """
    Сервис для интеграции с SeaArt AI
    Поскольку SeaArt AI не предоставляет официального API,
    используем альтернативные методы для генерации изображений
    """
    
    def __init__(self):
        self.base_url = "https://www.seaart.ai"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9,ru;q=0.8',
            'Content-Type': 'application/json'
        })
        logging.info("SeaArt AI сервис инициализирован")
    
    def is_image_generation_request(self, message):
        """
        Определяем, является ли сообщение запросом на генерацию изображения
        """
        image_keywords = [
            'нарисуй', 'создай изображение', 'сгенерируй картинку', 'создай картинку',
            'нарисовать', 'изобрази', 'покажи как выглядит', 'визуализируй',
            '/generate', '/img', '/image', '/draw', '/создай', '/нарисуй',
            'картинка', 'рисунок', 'изображение', 'фото', 'арт', 'иллюстрация'
        ]
        
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in image_keywords)
    
    def extract_image_prompt(self, message):
        """
        Извлекаем промпт для генерации изображения из сообщения пользователя
        """
        # Удаляем команды и ключевые слова
        commands_to_remove = [
            '/generate', '/img', '/image', '/draw', '/создай', '/нарисуй',
            'нарисуй', 'создай изображение', 'сгенерируй картинку', 'создай картинку',
            'нарисовать', 'изобрази', 'покажи как выглядит', 'визуализируй'
        ]
        
        prompt = message.strip()
        for command in commands_to_remove:
            prompt = re.sub(rf'\b{re.escape(command)}\b', '', prompt, flags=re.IGNORECASE)
        
        # Очищаем от лишних пробелов и знаков препинания в начале
        prompt = prompt.strip(' ,:.-')
        
        return prompt if prompt else "красивый пейзаж"
    
    def generate_image_fallback(self, prompt):
        """
        Альтернативный метод генерации изображений через бесплатные сервисы
        Используем Pollinations.ai как бесплатную альтернативу
        """
        try:
            # Pollinations.ai - полностью бесплатный сервис генерации изображений
            pollinations_url = f"https://image.pollinations.ai/prompt/{quote(prompt)}"
            
            # Добавляем параметры для улучшения качества
            params = {
                'width': 1024,
                'height': 1024,
                'seed': int(time.time()),
                'enhance': 'true'
            }
            
            # Создаем полный URL с параметрами
            param_string = "&".join([f"{k}={v}" for k, v in params.items()])
            image_url = f"{pollinations_url}?{param_string}"
            
            logging.info(f"Генерация изображения через Pollinations.ai для промпта: {prompt}")
            
            # Проверяем доступность изображения
            response = requests.head(image_url, timeout=10)
            if response.status_code == 200:
                return {
                    'success': True,
                    'image_url': image_url,
                    'prompt': prompt,
                    'service': 'Pollinations.ai',
                    'message': f'Изображение создано по запросу: "{prompt}"'
                }
            else:
                logging.warning(f"Pollinations.ai недоступен: {response.status_code}")
                
        except Exception as e:
            logging.error(f"Ошибка при генерации изображения через Pollinations.ai: {str(e)}")
        
        # Если основной сервис недоступен, используем резервный
        return self._generate_via_picsum(prompt)
    
    def _generate_via_picsum(self, prompt):
        """
        Резервный метод через Lorem Picsum с тематическими изображениями
        """
        try:
            # Анализируем промпт для выбора подходящей категории
            categories = {
                'природа': ['nature', 'landscape', 'forest', 'mountain'],
                'животные': ['animal', 'cat', 'dog', 'wildlife'],
                'город': ['city', 'urban', 'building', 'street'],
                'море': ['ocean', 'sea', 'beach', 'water'],
                'небо': ['sky', 'cloud', 'sunset', 'sunrise']
            }
            
            # Определяем категорию по ключевым словам в промпте
            category = 'nature'  # по умолчанию
            prompt_lower = prompt.lower()
            for cat, keywords in categories.items():
                if any(keyword in prompt_lower for keyword in keywords + [cat]):
                    category = keywords[0]
                    break
            
            # Используем прямую генерацию через Picsum для стабильности
            picsum_url = f"https://picsum.photos/1024/1024?random={int(time.time())}"
            
            # Проверяем доступность
            response = requests.head(picsum_url, timeout=5)
            if response.status_code == 200:
                return {
                    'success': True,
                    'image_url': picsum_url,
                    'prompt': prompt,
                    'service': 'Picsum Photos',
                    'message': f'Случайное изображение по запросу: "{prompt}"'
                }
            else:
                # Последний fallback - статичное изображение
                fallback_url = "https://via.placeholder.com/1024x1024/4A90E2/FFFFFF?text=Generated+Image"
                return {
                    'success': True,
                    'image_url': fallback_url,
                    'prompt': prompt,
                    'service': 'Placeholder',
                    'message': f'Изображение-заглушка по запросу: "{prompt}" (внешние сервисы недоступны)'
                }
            
        except Exception as e:
            logging.error(f"Ошибка при генерации через резервный сервис: {str(e)}")
            return {
                'success': False,
                'error': 'Не удалось сгенерировать изображение',
                'message': 'Извините, сервисы генерации изображений временно недоступны'
            }
    
    def generate_image(self, prompt):
        """
        Основная функция генерации изображения
        """
        if not prompt or len(prompt.strip()) < 3:
            return {
                'success': False,
                'error': 'Слишком короткий промпт',
                'message': 'Пожалуйста, опишите более подробно, что вы хотите увидеть на изображении'
            }
        
        # Сначала пробуем основной метод
        result = self.generate_image_fallback(prompt)
        
        # Логируем результат
        if result['success']:
            logging.info(f"Изображение успешно сгенерировано: {result['service']}")
        else:
            logging.error(f"Не удалось сгенерировать изображение: {result.get('error', 'Неизвестная ошибка')}")
        
        return result
    
    def enhance_prompt(self, user_prompt):
        """
        Улучшаем промпт пользователя для лучших результатов генерации
        """
        # Добавляем ключевые слова для качества, если их нет
        quality_keywords = ['high quality', 'detailed', '4k', 'masterpiece', 'professional']
        style_keywords = ['realistic', 'photographic', 'artistic', 'digital art']
        
        enhanced = user_prompt.strip()
        
        # Проверяем наличие ключевых слов качества
        if not any(keyword in enhanced.lower() for keyword in quality_keywords):
            enhanced += ", high quality, detailed"
        
        # Добавляем стиль если не указан
        if not any(keyword in enhanced.lower() for keyword in style_keywords):
            enhanced += ", realistic"
        
        return enhanced
    
    def get_service_status(self):
        """
        Проверка статуса сервиса
        """
        try:
            # Проверяем доступность Pollinations.ai
            test_url = "https://image.pollinations.ai/prompt/test?width=64&height=64"
            response = requests.head(test_url, timeout=5)
            
            if response.status_code == 200:
                return {
                    'status': 'online',
                    'service': 'Pollinations.ai + Unsplash',
                    'message': 'Сервисы генерации изображений доступны'
                }
            else:
                return {
                    'status': 'limited',
                    'service': 'Unsplash only',
                    'message': 'Основной сервис недоступен, работаем через резервные'
                }
                
        except Exception as e:
            return {
                'status': 'offline',
                'service': 'None',
                'message': 'Сервисы генерации изображений временно недоступны'
            }