import random
import re
import sqlite3
import requests
from bs4 import BeautifulSoup

main_url = "https://db.chgk.info/random/types12/"


# Инициализация базы данных
def init_db(db_questions_name):
    conn = sqlite3.connect(db_questions_name)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT UNIQUE,
            answer TEXT,
            released INTEGER
        )
    """)
    conn.commit()
    conn.close()


# Проверка наличия вопроса в базе данных
def is_question_in_db(db_questions_name, question):
    conn = sqlite3.connect(db_questions_name)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM questions WHERE question = ?", (question,))
    result = cursor.fetchone()
    conn.close()
    return result is not None


def save_to_db(db_questions_name, question, answer):
    if is_question_in_db(db_questions_name, question):
        print("Вопрос уже существует в базе данных.")
        return

    conn = sqlite3.connect(db_questions_name)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO questions (question, answer, released) VALUES (?, ?, 0)", (question, answer))
        conn.commit()
    except sqlite3.IntegrityError:
        print("Вопрос уже существует в базе данных.")
    conn.close()


def get_random_question(db_questions_name):
    global count
    tail = str(random.randint(1, 3000000000))
    url = main_url + tail
    req = requests.get(url)
    site = BeautifulSoup(req.text, "lxml")
    questions = site.find_all("div", class_="random_question")
    for question in questions:
        if question.find("img") != None:
            continue
        strong_tag = question.find('strong')
        text_parts = []
        for sibling in strong_tag.next_siblings:
            if sibling.name == 'div' and 'collapsible' in sibling.get('class', []):
                break
            if sibling.name or sibling.strip():
                text_parts.append(
                    sibling.get_text(strip=True).replace("\n", " ") if sibling.name else sibling.strip().replace("\n",
                                                                                                                 " "))
        question_text = '\n'.join(text_parts)
        question_text = re.sub(r"(Раздаточный материал)", r"\1:\n", question_text, count=1)
        ansver_ps = question.find("div", class_="collapsible").find_all("p")
        if len(ansver_ps[0].text.split()) > 3:
            return
        answer_text = ""
        for p in ansver_ps:
            if any(keyword in p.text for keyword in ["Ответ:", "Комментарий:"]):
                answer_text += p.text.strip().replace("\n", " ") + "\n"
            answer_text = answer_text.replace("Ответ: ", "")

        print("Question:", question_text, '\n', 'Answer:', answer_text, '\n\n')
        save_to_db(db_questions_name, question_text, answer_text)
        count += 1


def get_question_by_id(db_questions_name, question_id):
    conn = sqlite3.connect(db_questions_name)
    cursor = conn.cursor()
    cursor.execute("SELECT question, answer FROM questions WHERE id = ?", (question_id,))
    result = cursor.fetchone()
    conn.close()
    if result:
        return result[0], result[1]
    else:
        return "Вопрос не найден", ""


init_db("questions_new.db")

count = 0
for i in range(300):
    get_random_question("questions_new.db")

print(count)
