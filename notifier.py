# notifier.py

import requests
from datetime import datetime
import pytz

# Telegram bot token and channel ID
TELEGRAM_TOKEN = "7819951392:AAFkYd9-sblexjXNqgIfhbWAIC1Lr6NmPpo"
CHANNEL_ID = "-1006734231237"  # Use -100 prefix for channels

# Format the signal message to look nice on Telegram
def format_signal_message(signal):
    johannesburg_time = datetime.fromtimestamp(signal['timestamp'], pytz.timezone('Africa/Johannesburg'))
    time_str = johannesburg_time.strftime('%Y-%m-%d %H:%M:%S')

    return (
        f"📡 *New Signal Detected!*\n\n"
        f"📊 Pattern: *{signal.get('pattern', 'Unknown')}*\n"
        f"📈 Direction: *{signal.get('direction', 'N/A').upper()}*\n"
        f"🎯 Entry Price: `{signal.get('entry')}`\n"
        f"✅ Take Profit: `{signal.get('tp')}`\n"
        f"🛑 Stop Loss: `{signal.get('sl')}`\n"
        f"⏰ Time: `{time_str}`"
    )

# Send signal to Telegram channel
def send_signal_to_telegram(signal):
    message = format_signal_message(signal)
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHANNEL_ID,
        "text": message,
        "parse_mode": "Markdown"
    }

    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        print("[Telegram] ✅ Signal sent successfully.")
    except requests.exceptions.RequestException as e:
        print(f"[Telegram] ❌ Failed to send signal: {e}")
