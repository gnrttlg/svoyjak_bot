import sqlite3


class QuestionsDb(object):
    def __init__(self, db_questions_name="questions.db"):
        self.question_conn = sqlite3.connect(db_questions_name)
        self.question_cursor = self.question_conn.cursor()
        self.question_cursor.execute("""CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT UNIQUE,
            answer TEXT,
            released INTEGER
        )""")
        self.question_conn.commit()

    def get_next_question(self):
        self.close_current_questions()
        self.question_cursor.execute("""
            WITH selected_question AS (
                SELECT id, question, answer
                FROM questions
                WHERE released = 0
                ORDER BY id ASC
                LIMIT 1
            )
            UPDATE questions
            SET released = 1
            WHERE id IN (SELECT id FROM selected_question)
            RETURNING id, question, answer
            """)
        return self.question_cursor.fetchone()

    def is_question_opened(self, question_id):
        self.question_cursor.execute("SELECT released FROM questions WHERE id = ?", (question_id,))
        result = self.question_cursor.fetchone()
        return result[0] == 1 if result is not None else False

    def get_current_answer(self):
        self.question_cursor.execute("SELECT answer FROM questions WHERE released = ? ORDER BY id DESC LIMIT 1", (1,))
        result = self.question_cursor.fetchone()
        return result[0] if result is not None else "Открытых вопросов нет в базе"

    def close_current_questions(self):
        self.question_cursor.execute("UPDATE questions SET released = 2 WHERE released = ?",
                                     (1,))
        self.question_conn.commit()


class UsersDb(object):
    def __init__(self, db_users_name="bot_users.db"):
        self.user_conn = sqlite3.connect(db_users_name)
        self.user_cursor = self.user_conn.cursor()
        self.user_cursor.execute("""CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            correct_answers INTEGER
        )""")
        self.user_conn.commit()

    def add_point(self, user_id, username):
        self.user_cursor.execute(
            """INSERT INTO users (user_id, username, correct_answers)
               VALUES (?, ?, 1)
               ON CONFLICT(user_id) DO UPDATE SET correct_answers = correct_answers + 1""",
            (user_id, username)
        )
        self.user_conn.commit()

    def get_stats(self):
        self.user_cursor.execute("SELECT username, correct_answers FROM users ORDER BY correct_answers DESC")
        return self.user_cursor.fetchall()
