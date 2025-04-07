# MongoDB Backup System

A professional MongoDB backup solution that automatically dumps databases, compresses them, uploads to Cloudflare R2 storage, and sends status notifications via Telegram.

## Features

- 🗄️ Full MongoDB database backup
- 🗜️ Maximum compression to save storage space
- ☁️ Secure upload to Cloudflare R2 storage
- 📱 Real-time status updates via Telegram
- 📊 Progress tracking for large backups
- 🔄 Automatic cleanup of temporary files

## Project Structure

The project is organized into multiple Python files for better maintainability:

- `main.py` - Main script that orchestrates the backup process
- `config.py` - Configuration settings for R2 and Telegram
- `backup_manager.py` - Handles database dumps, compression, and uploads
- `telegram_notifier.py` - Manages Telegram notifications
- `progress_tracker.py` - Tracks and reports upload progress
- `requirements.txt` - List of required Python packages

## Requirements

- Python 3.8+
- MongoDB installed and accessible
- Cloudflare R2 storage account
- Telegram bot token and channel

## Installation

1. Clone the repository:
```bash
git clone https://github.com/AppleEcosystem/MongodBackup.git
```

2. Install required packages
```bash
pip3 install -r requirements
```

## Configuration

Edit the `config.py` file to set your credentials:

```python
# R2 Configuration
R2_BUCKET = 'backups'  # Your R2 bucket name
R2_ENDPOINT = 'https://your-account-id.r2.cloudflarestorage.com'
R2_ACCESS_KEY_ID = 'your-access-key'
R2_SECRET_ACCESS_KEY = 'your-secret-key'

# Telegram Configuration
TELEGRAM_TOKEN = 'your-telegram-bot-token'
TELEGRAM_CHANNEL_ID = 'your-channel-id'
TELEGRAM_API_URL = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}
