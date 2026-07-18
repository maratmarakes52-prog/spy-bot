import telebot
from telebot import types
import sqlite3
import threading
import time
from datetime import datetime

# ===== КОНФИГ =====
BOT_TOKEN = "8691007369:AAEpugKsGg_eBPbchs8MCxc_jGoE2asX6ak"
ADMIN_ID = 7481288398

bot = telebot.TeleBot(BOT_TOKEN)

# ===== БАЗА ДАННЫХ =====
conn = sqlite3.connect('spy_data.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id INTEGER,
        message_id INTEGER,
        user_id INTEGER,
        username TEXT,
        text TEXT,
        file_id TEXT,
        file_type TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')
conn.commit()

# ===== СОХРАНЕНИЕ =====
def save_message(message):
    user_id = message.from_user.id
    username = message.from_user.username or "no_username"
    chat_id = message.chat.id
    msg_id = message.message_id
    text = message.text or ""

    file_id = None
    file_type = None
    if message.photo:
        file_id = message.photo[-1].file_id
        file_type = "photo"
    elif message.video:
        file_id = message.video.file_id
        file_type = "video"
    elif message.document:
        file_id = message.document.file_id
        file_type = "document"
    elif message.audio:
        file_id = message.audio.file_id
        file_type = "audio"
    elif message.voice:
        file_id = message.voice.file_id
        file_type = "voice"
    elif message.video_note:
        file_id = message.video_note.file_id
        file_type = "video_note"

    cursor.execute('''
        INSERT INTO messages (chat_id, message_id, user_id, username, text, file_id, file_type)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (chat_id, msg_id, user_id, username, text, file_id, file_type))
    conn.commit()

def get_message_by_id(msg_id, chat_id):
    cursor.execute('''
        SELECT user_id, username, text, file_id, file_type 
        FROM messages 
        WHERE message_id = ? AND chat_id = ?
        ORDER BY created_at DESC LIMIT 1
    ''', (msg_id, chat_id))
    return cursor.fetchone()

def delete_message_from_db(msg_id, chat_id):
    cursor.execute('DELETE FROM messages WHERE message_id = ? AND chat_id = ?', (msg_id, chat_id))
    conn.commit()

def get_all_messages():
    cursor.execute('''
        SELECT chat_id, message_id, user_id, username, text, file_id, file_type 
        FROM messages 
        WHERE user_id != ?
    ''', (ADMIN_ID,))
    return cursor.fetchall()

# ===== ПЕРЕХВАТ НОВЫХ =====
@bot.message_handler(content_types=['text', 'photo', 'video', 'document', 'audio', 'voice', 'video_note'])
def catch_all_messages(message):
    if message.from_user.id == ADMIN_ID:
        return
    save_message(message)

# ===== ИЗМЕНЕНИЯ =====
@bot.edited_message_handler()
def handle_edit(message):
    if message.from_user.id == ADMIN_ID:
        return

    chat_id = message.chat.id
    msg_id = message.message_id
    new_text = message.text or ""

    old = get_message_by_id(msg_id, chat_id)

    if old:
        old_user_id, old_username, old_text, old_file_id, old_file_type = old

        if old_text and old_text != new_text:
            user_first_name = message.from_user.first_name or "User"
            user_username = message.from_user.username or "no_username"
            
            bot.send_message(
                ADMIN_ID,
                f"￴￴￴{user_first_name} (@{user_username}) изменил(а) сообщение:\n\n"
                f"Old:\n{old_text}\n\n"
                f"New:\n{new_text}"
            )

        delete_message_from_db(msg_id, chat_id)
        save_message(message)

# ===== ФОНОВОЕ ОТСЛЕЖИВАНИЕ УДАЛЕНИЙ =====
def check_deleted_messages():
    while True:
        try:
            all_msgs = get_all_messages()
            
            for chat_id, msg_id, user_id, username, text, file_id, file_type in all_msgs:
                try:
                    bot.get_chat(chat_id)
                except Exception as e:
                    if "message to delete not found" in str(e).lower() or "message not found" in str(e).lower():
                        try:
                            user = bot.get_chat(user_id)
                            user_first_name = user.first_name or "User"
                            user_username = user.username or "no_username"
                        except:
                            user_first_name = username
                            user_username = username

                        if text:
                            bot.send_message(
                                ADMIN_ID,
                                f"￴￴￴{user_first_name} (@{user_username}) удалил(а) сообщение:\n\n{text}"
                            )
                        elif file_id and file_type:
                            file_type_map = {
                                "photo": "Фото",
                                "video": "Видео",
                                "document": "Документ",
                                "audio": "Аудио",
                                "voice": "Голосовое",
                                "video_note": "Видео-сообщение"
                            }
                            bot.send_message(
                                ADMIN_ID,
                                f"￴￴￴{user_first_name} (@{user_username}) удалил(а) {file_type_map.get(file_type, 'Медиа')}"
                            )
                        
                        delete_message_from_db(msg_id, chat_id)
                        
            time.sleep(2)
            
        except Exception as e:
            print(f"Ошибка: {e}")
            time.sleep(5)

# ===== ЗАПУСК ФОНА =====
thread = threading.Thread(target=check_deleted_messages, daemon=True)
thread.start()

# ===== /START (ОБНОВЛЁННЫЙ) =====
@bot.message_handler(commands=['start'])
def start(message):
    markup = types.InlineKeyboardMarkup()
    btn = types.InlineKeyboardButton(
        text="🔘 Включить управление чатами",
        url=f"https://t.me/{bot.get_me().username}?startgroup=start"
    )
    markup.add(btn)

    bot.send_message(
        message.chat.id,
        "🤖 **Я — Spy Bot**\n\n"
        "📌 Сохраняю ВСЕ сообщения в твоих чатах\n"
        "📌 Слежу за изменениями и удалениями\n"
        "📌 Могу сохранять самоуничтожающиеся медиа\n\n"
        "👇 Нажми кнопку, чтобы включить меня в чате:",
        parse_mode="Markdown",
        reply_markup=markup
    )

# ===== ЗАПУСК =====
if __name__ == "__main__":
    print("🕵️ SPY BOT ЗАПУЩЕН!")
    bot.polling(non_stop=True)
