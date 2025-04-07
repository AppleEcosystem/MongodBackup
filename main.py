#!/usr/bin/env python3
import os
import asyncio
import logging
from telegram_notifier import TelegramNotifier
from backup_manager import BackupManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    # Initialize components
    telegram = TelegramNotifier()
    backup = BackupManager(telegram)
    
    try:
        # 1. Dump MongoDB
        if not await backup.dump_mongodb():
            raise Exception("Database dump failed")

        # 2. Create ZIP
        if not await backup.create_max_compression_zip():
            raise Exception("ZIP creation failed")

        # 3. Upload to R2
        if not await backup.upload_to_r2():
            raise Exception("Upload failed")

        # 4. Cleanup (preserve ZIP for final message)
        cleanup_error = await backup.cleanup()
        if cleanup_error:
            raise Exception(f"Cleanup failed: {cleanup_error}")

        # 5. Final success message
        await telegram.send_final_message(True)
        logger.info("🚀 Backup completed successfully")

        # 6. Now safe to remove the ZIP file
        if os.path.exists(backup.backup_zip):
            os.remove(backup.backup_zip)

    except Exception as e:
        logger.error(f"💥 Backup failed: {str(e)}")
        await telegram.send_final_message(False, str(e))

if __name__ == "__main__":
    asyncio.run(main())
