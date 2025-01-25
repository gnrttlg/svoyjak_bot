import asyncio
import random
import re
from datetime import datetime, time, timedelta
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.types import FSInputFile
from aiogram.filters.command import Command
import logging
from check_answer import check_strings
from text_to_image import create_question_image
from db_process import UsersDb, QuestionsDb
from daily_tracking import DailyTracker
import json
import os

os.makedirs("questions_images", exist_ok=True)
logging.basicConfig(level=logging.DEBUG)

if os.path.exists("config.json"):
    with open("config.json", "r") as f:
        config = json.load(f)

API_TOKEN = config["API_TOKEN"]
GROUP_ID = config["GROUP_ID"]
BOT_USERNAME = config["BOT_USERNAME"]

class BotState:
    def __init__(self):
        self.current_question = None
        self.accepting_answers = False
        self.daily_count = 0
        self.min_interval = 30
        self.max_interval = 70
        self.is_day_ended = False
        # Тестовые значения
        # self.min_interval = 1
        # self.max_interval = 2


bot_state = BotState()
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Подключение к базам данных
users_db = UsersDb()
questions_db = QuestionsDb("questions_new.db")
daily_tracker = DailyTracker("daily_stats.json")


async def send_question():
    question = questions_db.get_next_question()
    if question:
        question_id, question_text, question_answer = question
        bot_state.current_question = question_id
        bot_state.accepting_answers = True
        image_path = create_question_image(question_text, question_id)
        if not os.path.exists(image_path):
            await bot.send_message(chat_id=GROUP_ID, text="Не удалось создать изображение для вопроса.")
            return
        image_file = FSInputFile(image_path)
        await bot.send_photo(chat_id=GROUP_ID, photo=image_file, caption=f"qid: {question_id}")
    else:
        await bot.send_message(chat_id=GROUP_ID, text="Вопросы закончились. Добавьте новые в базу данных.")


@dp.message(F.reply_to_message)
async def check_answer(message: Message):
    reply_message = message.reply_to_message
    if reply_message.from_user.username != BOT_USERNAME or reply_message.caption == None:
        return
    question_text = reply_message.caption
    match = re.match(r"qid: (\d+)", question_text)
    if not match:
        return
    question_id = int(match.group(1))
    if not bot_state.accepting_answers or not questions_db.is_question_opened(question_id):
        await message.reply("Вопрос уже закрыт!")
        return
    result = questions_db.get_current_answer()
    if result:
        correctness = check_strings(message.text.lower().strip(), result)
        if correctness == 2:
            bot_state.accepting_answers = False
            questions_db.close_current_questions()
            await message.reply(f"Правильно! \n{result}")
            users_db.add_point(message.from_user.id, message.from_user.username)
        elif correctness == 1:
            await message.reply("Есть частичное совпадение с ответом, но этого недотаточно.")
        else:
            await message.reply("Неправильно, попробуйте ещё раз.")
    else:
        await message.reply("Ответ для этого вопроса не найден в базе данных.")


@dp.message(Command("stats"))
async def show_stats(message: Message):
    all_users = users_db.get_stats()
    if all_users:
        stats = "Топ-10 пользователей:\n" + "\n".join(
            [f"{i + 1}. {user[0]}: {user[1]} правильных ответов" for i, user in enumerate(all_users[:10])])
    else:
        stats = "Рейтинг пока пуст."
    await message.reply(stats)


@dp.message(Command("my_stats"))
async def show_my_stats(message: Message):
    all_users = users_db.get_stats()
    for position, user in enumerate(all_users, start=1):
        if user[0] == message.from_user.username:
            await message.reply(f"Вы на {position}-м месте с {user[1]} правильными ответами.")
            return
    await message.reply("Вы ещё не участвовали в викторине.")


async def schedule_posting():
    start_hour = 7
    question_point = datetime.combine(datetime.today(), time(start_hour, random.randint(0, bot_state.min_interval)))
    terminal_time = time(23, 00)
    end_time = time(23, 30)
    while True:
        now = datetime.now()
        current_time = now.time()
        if question_point.time() <= current_time <= terminal_time:
            bot_state.is_day_ended = False
            delta = timedelta(minutes=random.randint(bot_state.min_interval, bot_state.max_interval))
            question_point = now + delta
            if question_point.time() > terminal_time or question_point.time() < time(start_hour, 0):
                question_point = datetime.combine(datetime.today(), end_time)
            if bot_state.accepting_answers:
                bot_state.accepting_answers = False
                try:
                    answer = questions_db.get_current_answer()
                    if answer:
                        result = "Ответ на предыдущий вопрос: " + answer
                        questions_db.close_current_questions()
                        await bot.send_message(chat_id=GROUP_ID, text=result)
                except Exception:
                    logging.debug(f"Ошибка доступа к базе в {current_time}")
            daily_tracker.increment_daily_counter()
            try:
                await bot.send_message(chat_id=GROUP_ID,
                                       text=f"⚠ Внимание! Вопрос дня №{daily_tracker.get_daily_count()}. Ответы присылайте реплаем на "
                                            f"вопрос.")
                await send_question()
            except Exception:
                logging.debug(f"Не получилось отправить вопрос в {current_time}")
            logging.debug(f"Следующий вопрос будет задан в {question_point.time()}")

        if end_time <= current_time and not bot_state.is_day_ended:
            bot_state.is_day_ended = True
            if bot_state.accepting_answers:
                bot_state.accepting_answers = False
                try:
                    answer = questions_db.get_current_answer()
                    if answer:
                        result = "Ответ на предыдущий вопрос: " + answer
                        questions_db.close_current_questions()
                        await bot.send_message(chat_id=GROUP_ID, text=result)
                except Exception:
                    logging.debug("Ошибка доступа к базе в конце дня")
            try:
                if daily_tracker.get_daily_count() > 0:
                    await bot.send_message(chat_id=GROUP_ID,
                                           text=f"Вопросы на сегодня закончились. Задано вопросов: {daily_tracker.get_daily_count()}.")
            except Exception:
                logging.debug("Не получилось отправить статистику дня")
            question_point = datetime.combine(datetime.today(), time(7, random.randint(0, 30)))
            logging.debug(f"На следующий день вопрос будет задан в {question_point.time()}")

        wait_time = (question_point - datetime.now()).total_seconds()

        await asyncio.sleep(wait_time)


async def shutdown():
    users_db.user_conn.close()
    questions_db.question_conn.close()


async def main():
    asyncio.create_task(schedule_posting())
    await dp.start_polling(bot, skip_updates=True, on_shutdown=shutdown)


if __name__ == "__main__":
    asyncio.run(main())
