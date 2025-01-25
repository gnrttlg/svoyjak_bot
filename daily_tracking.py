import json
import os
from datetime import datetime


class DailyTracker:
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
            json.dump(self.stats, f)

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

