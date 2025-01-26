import json
import os
from datetime import datetime


class BaseTracker:
    def __init__(self, file_path):
        self.file_path = file_path
        self.stats = self.load_stats()

    def load_stats(self):
        if os.path.exists(self.file_path):
            with open(self.file_path, "r") as f:
                return json.load(f)
        return {}

    def save_stats(self):
        with open(self.file_path, "w") as f:
            json.dump(self.stats, f, indent=4)

    def clean_stats(self):
        self.stats = {}
        self.save_stats()


class DailyTracker(BaseTracker):
    def increment_daily_counter(self):
        today = datetime.now().strftime("%Y-%m-%d")
        if today in self.stats:
            self.stats[today] += 1
        else:
            self.stats[today] = 1
        self.save_stats()

    def get_daily_count(self):
        today = datetime.now().strftime("%Y-%m-%d")
        return self.stats.get(today, 0)


class DailyChampTracker(BaseTracker):
    def increment_daily_stats(self, username):
        if username in self.stats:
            self.stats[username] += 1
        else:
            self.stats[username] = 1
        self.save_stats()

    def get_champs_string(self):
        if not self.stats:
            return "Сегодня нет сильнейшего свойжака."

        max_value = max(self.stats.values())
        daily_champs = [key for key, value in self.stats.items() if value == max_value]

        if len(daily_champs) == 1:
            return f"Сильнейший свойжак дня - {daily_champs[0]} с {max_value} правильных ответов."
        else:
            champs_list = "\n".join(daily_champs)
            return f"Сильнейшие свойжаки дня, набравшие {max_value} правильных ответов:\n{champs_list}"
