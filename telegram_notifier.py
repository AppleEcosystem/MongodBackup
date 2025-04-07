#!/usr/bin/env python3
import logging
import requests
from config import TELEGRAM_API_URL, TELEGRAM_CHANNEL_ID

# Configure logging
logger = logging.getLogger(__name__)

class TelegramNotifier:
    def __init__(self):
        self.message_id = None
        self.last_update = 0
        self.backup_info = {}

    async def update_message(self, text):
        """Create or edit the status message"""
        try:
            url = f"{TELEGRAM_API_URL}/{'sendMessage' if not self.message_id else 'editMessageText'}"
            payload = {
                'chat_id': TELEGRAM_CHANNEL_ID,
                'text': text,
                'parse_mode': 'HTML'
            }
            if self.message_id:
                payload['message_id'] = self.message_id

            response = requests.post(url, json=payload, timeout=10).json()

            if response.get('ok'):
                if not self.message_id:
                    self.message_id = response['result']['message_id']
                return True
            logger.error(f"Telegram API error: {response.get('description')}")
        except Exception as e:
            logger.error(f"Telegram notification failed: {str(e)}")
        return False

    async def send_final_message(self, success, error=None):
        """Send final success/error message"""
        try:
            if success:
                text = (
                    "✅ <b>Backup Completed Successfully</b>\n\n"
                    f"📅 <b>Timestamp:</b> {self.backup_info['timestamp']}\n"
                    f"📦 <b>Backup Size:</b> {self.backup_info['size_mb']:.2f} MB\n"
                    f"📊 <b>Compression:</b> {self.backup_info['compression']:.1f}%\n"
                    f"🏷️ <b>File Name:</b> <code>{self.backup_info['filename']}</code>"
                )
            else:
                text = (
                    "❌ <b>Backup Failed</b>\n\n"
                    f"🛑 <b>Error:</b> <code>{error}</code>\n"
                    f"📅 <b>Timestamp:</b> {self.backup_info['timestamp']}"
                )
                if os.path.exists(self.backup_info.get('backup_path', '')):
                    text += f"\n\n⚠️ <b>Local Backup:</b> <code>{self.backup_info['backup_path']}</code>"

            return await self.update_message(text)
        except Exception as e:
            logger.error(f"Final message failed: {str(e)}")
            return False
