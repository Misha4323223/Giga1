import os
import logging
from flask import Flask, render_template, request, jsonify, session
from werkzeug.middleware.proxy_fix import ProxyFix
from gigachat_model import GigaChatModel
from seaart_service import SeaArtService

# Setup logging
logging.basicConfig(level=logging.DEBUG)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "your-secret-key-here")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Initialize GigaChat model and SeaArt service
ai_model = GigaChatModel()
image_service = SeaArtService()

@app.route('/')
def index():
    """Главная страница чата"""
    if 'chat_history' not in session:
        session['chat_history'] = []
    return render_template('chat.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    """API endpoint для отправки сообщений в чат"""
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return jsonify({'error': 'Сообщение не может быть пустым'}), 400
        
        # Получаем историю чата из сессии
        if 'chat_history' not in session:
            session['chat_history'] = []
        
        # Добавляем сообщение пользователя в историю
        session['chat_history'].append({
            'role': 'user',
            'content': user_message
        })
        
        # Проверяем, не запрос ли это на генерацию изображения
        if image_service.is_image_generation_request(user_message):
            # Извлекаем промпт для генерации изображения
            image_prompt = image_service.extract_image_prompt(user_message)
            
            # Генерируем изображение
            image_result = image_service.generate_image(image_prompt)
            
            if image_result['success']:
                response_message = image_result['message']
                
                # Добавляем специальный ответ с изображением
                session['chat_history'].append({
                    'role': 'assistant',
                    'content': response_message,
                    'type': 'image',
                    'image_url': image_result['image_url'],
                    'prompt': image_result['prompt'],
                    'service': image_result['service']
                })
                
                session.modified = True
                
                logging.info(f"Отправляю изображение: {image_result['image_url']}")
                
                return jsonify({
                    'response': response_message,
                    'type': 'image',
                    'image_url': image_result['image_url'],
                    'prompt': image_result['prompt'],
                    'service': image_result['service'],
                    'status': 'success'
                })
            else:
                error_message = image_result['message']
                session['chat_history'].append({
                    'role': 'assistant',
                    'content': error_message
                })
                
                session.modified = True
                
                return jsonify({
                    'response': error_message,
                    'status': 'error'
                })
        
        # Обычная генерация текстового ответа от AI
        ai_response = ai_model.generate_response(user_message, session['chat_history'])
        
        # Добавляем ответ AI в историю
        session['chat_history'].append({
            'role': 'assistant',
            'content': ai_response
        })
        
        # Ограничиваем историю последними 20 сообщениями для экономии памяти
        if len(session['chat_history']) > 20:
            session['chat_history'] = session['chat_history'][-20:]
        
        session.modified = True
        
        return jsonify({
            'response': ai_response,
            'status': 'success'
        })
        
    except Exception as e:
        logging.error(f"Ошибка при обработке сообщения: {str(e)}")
        return jsonify({
            'error': 'Произошла ошибка при генерации ответа. Попробуйте еще раз.',
            'status': 'error'
        }), 500

@app.route('/api/clear', methods=['POST'])
def clear_chat():
    """Очистка истории чата"""
    session['chat_history'] = []
    session.modified = True
    return jsonify({'status': 'success', 'message': 'История чата очищена'})

@app.route('/api/history', methods=['GET'])
def get_history():
    """Получение истории чата"""
    history = session.get('chat_history', [])
    return jsonify({'history': history})

@app.route('/api/model_status', methods=['GET'])
def model_status():
    """Проверка статуса модели"""
    status = ai_model.get_status()
    return jsonify(status)

@app.route('/api/image_status', methods=['GET'])  
def image_status():
    """Проверка статуса сервиса генерации изображений"""
    status = image_service.get_service_status()
    return jsonify(status)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
