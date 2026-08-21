import asyncio
import logging
from pathlib import Path
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message, LabeledPrice, PreCheckoutQuery
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

TOKEN = "8677404297:AAF7GVe0eEMEwdQUYTzxEEC4tTpc0BC28cA"

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

VIDEOS = [
    "videos/video_1.mp4",
    "videos/video_2.mp4",
    "videos/video_3.mp4",
    "videos/video_4.mp4",
    "videos/video_5.mp4"
]

PRICE_STARS = 50

@dp.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        "Чтобы посмотреть фулл с катеджа Казани необходимо внести 50⭐️ для просмотра.",
        reply_markup=None
    )
    await bot.send_invoice(
        chat_id=message.chat.id,
        title="Доступ к видео с катеджа",
        description="5 эксклюзивных видео после оплаты",
        payload="catedge_kazan_access",
        currency="XTR",
        provider_token="",
        prices=[LabeledPrice(label="Доступ", amount=PRICE_STARS)],
    )

@dp.pre_checkout_query()
async def pre_checkout_query(pre_checkout_q: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_q.id, ok=True)

@dp.message(F.successful_payment)
async def successful_payment(message: Message):
    await message.answer("Оплата получена! Держи видео 👇")
    for video_path in VIDEOS:
        path = Path(video_path)
        if path.exists():
            await message.answer_video(video=path)
            await asyncio.sleep(0.5)
        else:
            await message.answer(f"Файл {video_path} не найден, проверь папку.")

async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())