#!/usr/bin/env python3
import time
from datetime import datetime

class ProgressTracker:
    def __init__(self, total_size, telegram_notifier):
        self.total_size = total_size
        self.uploaded = 0
        self.last_reported = 0
        self.telegram = telegram_notifier

    async def update(self, chunk_size):
        self.uploaded += chunk_size
        percent = (self.uploaded / self.total_size) * 100

        if percent - self.last_reported >= 5 or time.time() - self.telegram.last_update >= 30:
            status = (
                "🔄 <b>Backup in Progress</b>\n\n"
                f"📦 <b>Uploading:</b> {self.telegram.backup_info['filename']}\n"
                f"📊 <b>Progress:</b> {percent:.1f}% ({self.uploaded/1024/1024:.1f}MB/{self.total_size/1024/1024:.1f}MB)\n"
                f"⏱️ <b>Last Update:</b> {datetime.now().strftime('%H:%M:%S')}"
            )
            if await self.telegram.update_message(status):
                self.last_reported = percent
                self.telegram.last_update = time.time()
