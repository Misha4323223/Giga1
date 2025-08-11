import os
import requests
import json
import logging
import urllib.parse
from typing import Optional, Dict, Any
import re

class SearchService:
    def __init__(self):
        self.perplexity_api_key = os.environ.get("PERPLEXITY_API_KEY")
        self.yandex_api_key = os.environ.get("YANDEX_SEARCH_API_KEY")
        self.enabled = True  # Всегда включен - используем бесплатные источники
        
        available_services = ["DuckDuckGo", "Wikipedia"]
        if self.perplexity_api_key:
            available_services.append("Perplexity")
        if self.yandex_api_key:
            available_services.append("Яндекс.Поиск")
            
        logging.info(f"Поиск в интернете включен: {', '.join(available_services)}")
    
    def search(self, query: str) -> Optional[str]:
        """Поиск информации в интернете через бесплатные источники"""
        if not self.enabled:
            return None
        
        # Сначала пробуем платные API если есть ключи
        if self.yandex_api_key:
            result = self._search_yandex(query)
            if result:
                return result
                
        if self.perplexity_api_key:
            result = self._search_perplexity(query)
            if result:
                return result
        
        # Специальная обработка для погодных запросов
        if any(word in query.lower() for word in ['погода', 'температура', 'прогноз', 'климат']):
            result = self._search_weather_info(query)
            if result:
                return result
        
        # Для энциклопедических запросов - Wikipedia
        if any(word in query.lower() for word in ['что такое', 'кто такой', 'определение', 'история']):
            result = self._search_wikipedia(query)
            if result:
                return result
        
        # Основной поиск через DuckDuckGo
        result = self._search_duckduckgo(query)
        if result:
            return result
        
        # Если ничего не найдено, попробуем Wikipedia как запасной вариант
        result = self._search_wikipedia(query)
        if result:
            return result
        
        # Если совсем ничего не найдено, возвращаем информационное сообщение
        return f"🔍 **Поиск информации в интернете**\n\nК сожалению, в данный момент не удалось получить актуальную информацию по запросу '{query}' из доступных источников. Это может быть связано с временными ограничениями доступа к внешним сервисам."
    
    def _search_perplexity(self, query: str) -> Optional[str]:
        """Поиск через Perplexity API"""
        try:
            url = "https://api.perplexity.ai/chat/completions"
            
            headers = {
                'Authorization': f'Bearer {self.perplexity_api_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                "model": "llama-3.1-sonar-small-128k-online",
                "messages": [
                    {
                        "role": "system",
                        "content": "Ты помощник для поиска актуальной информации. Отвечай кратко и точно на русском языке."
                    },
                    {
                        "role": "user", 
                        "content": query
                    }
                ],
                "max_tokens": 500,
                "temperature": 0.2,
                "top_p": 0.9,
                "return_images": False,
                "return_related_questions": False,
                "search_recency_filter": "month",
                "stream": False
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=20)
            
            if response.status_code == 200:
                result = response.json()
                if 'choices' in result and len(result['choices']) > 0:
                    content = result['choices'][0]['message']['content']
                    
                    # Добавляем источники если есть
                    sources = ""
                    if 'citations' in result and result['citations']:
                        sources = "\n\n📚 Источники:\n" + "\n".join([f"• {url}" for url in result['citations'][:3]])
                    
                    return f"🔍 **Актуальная информация из интернета:**\n\n{content}{sources}"
                    
            logging.warning(f"Perplexity API вернул {response.status_code}")
            return None
            
        except Exception as e:
            logging.warning(f"Ошибка Perplexity API: {str(e)}")
            return None
    
    def _search_duckduckgo(self, query: str) -> Optional[str]:
        """Бесплатный поиск через DuckDuckGo Instant Answer API"""
        try:
            # DuckDuckGo Instant Answer API - полностью бесплатный
            encoded_query = urllib.parse.quote(query)
            url = f"https://api.duckduckgo.com/?q={encoded_query}&format=json&no_html=1&skip_disambig=1"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                # Формируем ответ из доступных данных
                result_parts = []
                
                # Основной ответ
                if data.get('AbstractText'):
                    result_parts.append(f"📋 **Краткая информация:**\n{data['AbstractText']}")
                
                # Определение
                if data.get('Definition'):
                    result_parts.append(f"📖 **Определение:**\n{data['Definition']}")
                
                # Связанные темы
                if data.get('RelatedTopics'):
                    topics = []
                    for topic in data['RelatedTopics'][:3]:
                        if isinstance(topic, dict) and topic.get('Text'):
                            topics.append(f"• {topic['Text'][:100]}...")
                    if topics:
                        result_parts.append(f"🔗 **Связанные темы:**\n" + "\n".join(topics))
                
                # Ответ
                if data.get('Answer'):
                    result_parts.append(f"💡 **Быстрый ответ:**\n{data['Answer']}")
                
                if result_parts:
                    result = "\n\n".join(result_parts)
                    
                    # Добавляем источник
                    if data.get('AbstractURL'):
                        result += f"\n\n📚 **Источник:** {data['AbstractURL']}"
                    
                    return f"🔍 **Информация из интернета:**\n\n{result}"
                
            return None
            
        except Exception as e:
            logging.error(f"Ошибка при поиске DuckDuckGo: {str(e)}")
            return None
    
    def _search_wikipedia(self, query: str) -> Optional[str]:
        """Поиск в Wikipedia API (бесплатно)"""
        try:
            # Wikipedia API - полностью бесплатный
            encoded_query = urllib.parse.quote(query)
            url = f"https://ru.wikipedia.org/api/rest_v1/page/summary/{encoded_query}"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (ChatBot/1.0)'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('extract'):
                    title = data.get('title', 'Статья')
                    extract = data['extract']
                    page_url = data.get('content_urls', {}).get('desktop', {}).get('page', '')
                    
                    result = f"📖 **{title}**\n\n{extract}"
                    if page_url:
                        result += f"\n\n📚 **Источник:** {page_url}"
                    
                    return f"🔍 **Информация из Wikipedia:**\n\n{result}"
            
            return None
            
        except Exception as e:
            logging.error(f"Ошибка при поиске Wikipedia: {str(e)}")
            return None
    
    def _search_yandex(self, query: str) -> Optional[str]:
        """Поиск через Яндекс.Поиск API"""
        try:
            # Яндекс XML API для поиска
            base_url = "https://yandex.com/search/xml"
            
            params = {
                'query': query,
                'user': 'chatbot',
                'key': self.yandex_api_key,
                'lr': 213,  # Москва
                'l10n': 'ru',
                'sortby': 'rlv',
                'filter': 'none',
                'maxpassages': 3,
                'groupby': 'attr%3Dd.mode%3Ddeep.groups-on-page%3D5.docs-in-group%3D1'
            }
            
            response = requests.get(base_url, params=params, timeout=15)
            
            if response.status_code == 200:
                # Парсим XML ответ
                import xml.etree.ElementTree as ET
                
                root = ET.fromstring(response.content)
                results = []
                
                # Извлекаем результаты поиска
                for group in root.findall('.//group'):
                    for doc in group.findall('.//doc'):
                        title_elem = doc.find('.//title')
                        url_elem = doc.find('.//url')
                        passage_elem = doc.find('.//passage')
                        
                        if title_elem is not None and passage_elem is not None:
                            title = title_elem.text or ''
                            url = url_elem.text if url_elem is not None else ''
                            passage = passage_elem.text or ''
                            
                            # Очищаем от HTML тегов
                            title = re.sub(r'<[^>]+>', '', title)
                            passage = re.sub(r'<[^>]+>', '', passage)
                            
                            results.append({
                                'title': title,
                                'url': url,
                                'snippet': passage
                            })
                
                if results:
                    result_text = "🔍 **Результаты поиска Яндекс:**\n\n"
                    
                    for i, result in enumerate(results[:3], 1):
                        result_text += f"**{i}. {result['title']}**\n"
                        result_text += f"{result['snippet']}\n"
                        if result['url']:
                            result_text += f"🔗 {result['url']}\n"
                        result_text += "\n"
                    
                    return result_text
                    
            logging.warning(f"Яндекс API вернул {response.status_code}")
            return None
            
        except Exception as e:
            logging.warning(f"Ошибка Яндекс API: {str(e)}")
            return None
    
    def _search_weather_info(self, query: str) -> Optional[str]:
        """Поиск информации о погоде через различные источники"""
        try:
            # Определяем город из запроса
            query_lower = query.lower()
            city = "Moscow"  # По умолчанию
            city_name_ru = "Москве"  # Для отображения
            
            # Словарь городов для более точного определения
            cities_map = {
                # Основные города
                "москва": ("Moscow", "Москве"),
                "moscow": ("Moscow", "Москве"),
                "питер": ("Saint Petersburg", "Санкт-Петербурге"),
                "спб": ("Saint Petersburg", "Санкт-Петербурге"),
                "санкт-петербург": ("Saint Petersburg", "Санкт-Петербурге"),
                "екатеринбург": ("Yekaterinburg", "Екатеринбурге"),
                "новосибирск": ("Novosibirsk", "Новосибирске"),
                "казань": ("Kazan", "Казани"),
                "казан": ("Kazan", "Казани"),
                "ростов": ("Rostov-on-Don", "Ростове-на-Дону"),
                "краснодар": ("Krasnodar", "Краснодаре"),
                "тула": ("Tula", "Туле"),
                "туле": ("Tula", "Туле"),
                "новомосковск": ("Novomoskovsk", "Новомосковске"),
                "якутск": ("Yakutsk", "Якутске"),
                "якутии": ("Yakutsk", "Якутии"),
                "мурманск": ("Murmansk", "Мурманске"),
                # Дальневосточные города
                "усурийск": ("Ussuriysk", "Усурийске"),
                "владивосток": ("Vladivostok", "Владивостоке"),
                "хабаровск": ("Khabarovsk", "Хабаровске"),
                "благовещенск": ("Blagoveshchensk", "Благовещенске"),
                "южно-сахалинск": ("Yuzhno-Sakhalinsk", "Южно-Сахалинске"),
                "петропавловск-камчатский": ("Petropavlovsk-Kamchatsky", "Петропавловске-Камчатском"),
                # Сибирские города
                "омск": ("Omsk", "Омске"),
                "красноярск": ("Krasnoyarsk", "Красноярске"),
                "барнаул": ("Barnaul", "Барнауле"),
                "кемерово": ("Kemerovo", "Кемерово"),
                "томск": ("Tomsk", "Томске"),
                "иркутск": ("Irkutsk", "Иркутске"),
                "улан-удэ": ("Ulan-Ude", "Улан-Удэ"),
                "чита": ("Chita", "Чите"),
                # Южные города
                "волгоград": ("Volgograd", "Волгограде"),
                "сочи": ("Sochi", "Сочи"),
                "ставрополь": ("Stavropol", "Ставрополе"),
                "астрахань": ("Astrakhan", "Астрахани"),
                # Поволжье
                "нижний новгород": ("Nizhny Novgorod", "Нижнем Новгороде"),
                "самара": ("Samara", "Самаре"),
                "уфа": ("Ufa", "Уфе"),
                "пермь": ("Perm", "Перми"),
                "саратов": ("Saratov", "Саратове"),
                # Центральные города
                "воронеж": ("Voronezh", "Воронеже"),
                "тверь": ("Tver", "Твери"),
                "ярославль": ("Yaroslavl", "Ярославле"),
                "рязань": ("Ryazan", "Рязани")
            }
            
            # Ищем город в запросе
            for city_key, (city_eng, city_ru) in cities_map.items():
                if city_key in query_lower:
                    city = city_eng
                    city_name_ru = city_ru
                    break
            
            # Попытка через wttr.in - бесплатный сервис погоды
            try:
                weather_url = f"https://wttr.in/{city}?format=j1"
                response = requests.get(weather_url, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    current = data.get('current_condition', [{}])[0]
                    
                    if current:
                        temp = current.get('temp_C', 'N/A')
                        feels_like = current.get('FeelsLikeC', 'N/A')
                        humidity = current.get('humidity', 'N/A')
                        wind = current.get('windspeedKmph', 'N/A')
                        desc = current.get('weatherDesc', [{}])[0].get('value', 'N/A')
                        
                        weather_info = f"""🌤️ **Актуальная погода в {city_name_ru}:**

**Сейчас:** {temp}°C (ощущается как {feels_like}°C)
**Описание:** {desc}
**Влажность:** {humidity}%
**Ветер:** {wind} км/ч

📊 **Источник:** wttr.in - актуальные метеоданные"""
                        
                        return weather_info
            except:
                pass
            
            # Fallback для случаев когда API недоступен
            return f"""🌤️ **Информация о погоде в {city_name_ru}:**

К сожалению, актуальные данные о погоде временно недоступны из-за ограничений API. 

💡 **Рекомендация:** Для получения точной актуальной погоды используйте:
• Приложение "Погода" на смартфоне
• Сайт Гидрометцентра России
• Yandex.Погода или другие специализированные сервисы"""
            
            return None
            
        except Exception as e:
            logging.error(f"Ошибка при поиске погоды: {str(e)}")
            return None
    
    def should_search(self, message: str) -> bool:
        """Определяет, нужен ли поиск для данного сообщения"""
        if not self.enabled:
            return False
            
        # Ключевые слова, указывающие на необходимость поиска
        search_indicators = [
            # Временные индикаторы
            "последние новости", "свежие новости", "что происходит",
            "актуальная информация", "сегодня", "вчера", "недавно",
            "текущий", "сейчас", "в настоящее время", "на данный момент",
            "2024", "2025", "этот год", "в этом году", "в прошлом году",
            
            # Финансовая и экономическая информация
            "курс", "цена", "стоимость", "котировки", "биржа", "акции",
            "криптовалюта", "биткоин", "доллар", "евро", "рубль",
            "инфляция", "экономика", "ВВП", "бюджет",
            
            # Погода и география
            "погода", "прогноз", "температура", "климат", "дождь", "снег",
            "ветер", "давление", "влажность",
            
            # Новости и события
            "что нового", "обновления", "изменения", "события", "произошло",
            "случилось", "новость", "сообщают", "объявили", "заявили",
            
            # Информационные запросы
            "что такое", "кто такой", "определение", "история", "биография",
            "расскажи о", "информация о", "данные о", "статистика",
            "рейтинг", "топ", "список", "обзор",
            
            # Технологии и наука
            "последняя версия", "обновление", "выпуск", "релиз",
            "исследование", "открытие", "изобретение", "патент",
            
            # Спорт и культура
            "результаты", "счет", "матч", "игра", "чемпионат",
            "фильм", "сериал", "книга", "музыка", "премьера",
            
            # Места и организации
            "работает", "открыт", "закрыт", "расписание", "адрес",
            "телефон", "сайт", "контакты", "время работы"
        ]
        
        message_lower = message.lower()
        return any(indicator in message_lower for indicator in search_indicators)
    
    def get_status(self) -> Dict[str, Any]:
        """Получение статуса сервиса поиска"""
        services = []
        if self.perplexity_api_key:
            services.append("Perplexity API")
        if self.yandex_api_key:
            services.append("Яндекс.Поиск")
        services.extend(["DuckDuckGo", "Wikipedia"])
        
        return {
            "enabled": self.enabled,
            "service": " + ".join(services),
            "message": "Поиск в интернете доступен (бесплатно)"
        }