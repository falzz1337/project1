from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import logging
from database_handler import db_manager

# Настройка логирования
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Разрешаем CORS для всех доменов

@app.route('/submit-application', methods=['POST'])
def submit_application():
    try:
        data = request.get_json()
        logger.debug(f"Получены данные: {data}")
        
        # Проверяем обязательные поля
        required_fields = ['firstName', 'lastName', 'phone', 'serviceType']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'success': False, 'message': f'Не заполнено поле: {field}'})
        
        # Добавляем заявку в базу данных
        success = db_manager.add_application(
            data['firstName'],
            data['lastName'],
            data['phone'],
            data['serviceType'],
            data.get('otherService')
        )
        
        if success:
            logger.info("Заявка успешно сохранена в базе данных")
            return jsonify({'success': True, 'message': 'Заявка успешно сохранена'})
        else:
            logger.error("Ошибка при сохранении заявки в базу данных")
            return jsonify({'success': False, 'message': 'Ошибка при сохранении заявки'})
    
    except Exception as e:
        logger.exception("Ошибка при обработке заявки")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/applications', methods=['GET'])
def get_applications():
    try:
        applications = db_manager.get_applications()
        return jsonify({'success': True, 'applications': applications})
    except Exception as e:
        logger.exception("Ошибка при получении заявок")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/health', methods=['GET'])
def health_check():
    """Проверка работоспособности сервера"""
    return jsonify({'status': 'ok', 'message': 'Сервер работает'})

@app.route('/db-path', methods=['GET'])
def db_path():
    """Показывает путь к базе данных"""
    import sqlite3
    return jsonify({'db_path': str(db_manager.conn)})

if __name__ == '__main__':
    print("Запуск сервера...")
    print("Проверьте доступность сервера по адресу: http://localhost:5000/health")
    print("Информация о базе данных: http://localhost:5000/db-path")
    app.run(host='localhost', port=5000, debug=True)