import asyncio
import sqlite3
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from database_handler import db_manager
from datetime import datetime
import pytz  # Добавляем импорт для работы с часовыми поясами

# Инициализация бота
bot = Bot(token='8179070735:AAFcGnoamLRMBBbvXCnsA6otC6xxIOY8pY0')
dp = Dispatcher()

# Список для хранения ID чатов пользователей
user_chats = set()

# Команда /start для подписки на уведомления
@dp.message(Command("start"))
async def start_command(message: types.Message):
    user_chats.add(message.chat.id)
    print(f"Новый подписчик: {message.chat.id} ({message.chat.first_name})")
    await message.answer("Вы подписались на уведомления о новых заявках!\n\nИспользуйте /help для просмотра всех команд.")

# Команда /stop для отписки от уведомлений
@dp.message(Command("stop"))
async def stop_command(message: types.Message):
    if message.chat.id in user_chats:
        user_chats.remove(message.chat.id)
        print(f"Пользователь отписался: {message.chat.id}")
        await message.answer("Вы отписались от уведомлений.")
    else:
        await message.answer("Вы не подписаны на уведомления.")

# Команда /status для проверки статуса
@dp.message(Command("status"))
async def status_command(message: types.Message):
    status = "подписан" if message.chat.id in user_chats else "не подписан"
    await message.answer(f"Вы {status} на уведомления. Всего подписчиков: {len(user_chats)}")

# Команда /help для показа всех команд
@dp.message(Command("help"))
async def help_command(message: types.Message):
    help_text = """
🤖 Доступные команды:

/start - Подписаться на уведомления о новых заявках
/stop - Отписаться от уведомлений
/status - Проверить статус подписки
/help - Показать это сообщение
/applications - Показать последние заявки (только для администраторов)

📋 Бот автоматически присылает уведомления о новых заявках с сайта.
"""
    await message.answer(help_text)

# Команда /applications для просмотра заявок (только для администратора)
@dp.message(Command("applications"))
async def applications_command(message: types.Message):
    # Здесь можно добавить проверку, является ли пользователь администратором
    # Например, if message.chat.id != ADMIN_ID: return
    
    try:
        applications = db_manager.get_applications()
        
        if not applications:
            await message.answer("Заявок пока нет.")
            return
        
        # Показываем только последние 5 заявок, чтобы не перегружать сообщение
        recent_apps = applications[:5]
        
        response = "📋 Последние заявки:\n\n"
        for app in recent_apps:
            app_id, first_name, last_name, phone, service_type, other_service, submission_date, notified = app
            
            # Преобразуем время из UTC в московское
            try:
                # Парсим время из базы данных (предполагается формат SQLite)
                utc_time = datetime.strptime(submission_date, "%Y-%m-%d %H:%M:%S")
                # Устанавливаем часовой пояс UTC
                utc_time = utc_time.replace(tzinfo=pytz.utc)
                # Конвертируем в московское время
                moscow_tz = pytz.timezone('Europe/Moscow')
                local_time = utc_time.astimezone(moscow_tz)
                # Форматируем время для отображения
                formatted_time = local_time.strftime("%d.%m.%Y %H:%M:%S")
            except:
                # Если не удалось преобразовать время, используем оригинальное
                formatted_time = submission_date
            
            response += f"#{app_id}: {first_name} {last_name}\n"
            response += f"📞 {phone}\n"
            response += f"🎯 {service_type}\n"
            if other_service:
                response += f"📝 {other_service}\n"
            response += f"⏰ {formatted_time}\n\n"
        
        if len(applications) > 5:
            response += f"... и еще {len(applications) - 5} заявок.\n\n"
            
        response += "Используйте /help для просмотра всех команд."
        
        await message.answer(response)
        
    except Exception as e:
        print(f"Ошибка при получении заявок: {e}")
        await message.answer("Произошла ошибка при получении заявок.")

# Функция для отправки уведомлений о новых заявках
async def send_new_applications():
    print("Запуск мониторинга новых заявок...")
    while True:
        try:
            # Получаем непрочитанные заявки
            applications = db_manager.get_unnotified_applications()
            
            if applications:
                print(f"Найдено {len(applications)} новых заявок")
            
            for app in applications:
                app_id, first_name, last_name, phone, service_type, other_service, submission_date, notified = app
                
                # Преобразуем время из UTC в московское
                try:
                    # Парсим время из базы данных
                    utc_time = datetime.strptime(submission_date, "%Y-%m-%d %H:%M:%S")
                    # Устанавливаем часовой пояс UTC
                    utc_time = utc_time.replace(tzinfo=pytz.utc)
                    # Конвертируем в московское время
                    moscow_tz = pytz.timezone('Europe/Moscow')
                    local_time = utc_time.astimezone(moscow_tz)
                    # Форматируем время для отображения
                    formatted_time = local_time.strftime("%d.%m.%Y %H:%M:%S")
                except:
                    # Если не удалось преобразовать время, используем оригинальное
                    formatted_time = submission_date
                
                # Формируем сообщение
                message_text = f"""
📋 Новая заявка #{app_id}

👤 Имя: {first_name} {last_name}
📞 Телефон: {phone}
🎯 Услуга: {service_type}
{"📝 Дополнительно: " + other_service if other_service else ""}
⏰ Дата: {formatted_time} (МСК)
                """
                
                print(f"Отправка уведомления о заявке #{app_id}")
                
                # Отправляем сообщение всем подписанным пользователям
                if not user_chats:
                    print("Нет подписчиков для отправки уведомлений")
                
                for chat_id in user_chats:
                    try:
                        await bot.send_message(chat_id, message_text)
                        print(f"Уведомление отправлено пользователю {chat_id}")
                    except Exception as e:
                        print(f"Ошибка отправки сообщения пользователю {chat_id}: {e}")
                
                # Помечаем заявку как отправленную
                db_manager.mark_as_notified(app_id)
            
            # Проверяем новые заявки каждые 5 секунд
            await asyncio.sleep(5)
            
        except Exception as e:
            print(f"Ошибка в send_new_applications: {e}")
            await asyncio.sleep(10)

async def main():
    print("Запуск Telegram бота...")
    print("Для подписки на уведомления отправьте боту команду /start")
    
    # Запускаем задачу отправки уведомлений
    asyncio.create_task(send_new_applications())
    
    # Запускаем бота
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Бот выключен')
    finally:
        db_manager.close()