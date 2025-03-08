import os
import requests
import websocket
import json
import logging
import time
import random
from dotenv import load_dotenv

load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get environment variables
GOTIFY_WS_URL = os.environ.get('GOTIFY_WS_URL')
TEAMS_WEBHOOK_URL = os.environ.get('TEAMS_WEBHOOK_URL')
GOTIFY_TOKEN = os.environ.get('GOTIFY_TOKEN')

if not TEAMS_WEBHOOK_URL:
    raise ValueError("TEAMS_WEBHOOK_URL environment variable is required")

if not GOTIFY_TOKEN:
    raise ValueError("GOTIFY_TOKEN environment variable is required")

if not GOTIFY_WS_URL:
    raise ValueError("GOTIFY_WS_URL environment variable is required")


# Add token to WebSocket URL
GOTIFY_WS_URL = f"{GOTIFY_WS_URL}?token={GOTIFY_TOKEN}"


def on_message_fetch_with_backoff(message, max_retries=5):
    retry_delay = 1  # Initial delay in seconds
    for attempt in range(max_retries):
        try:
            msg = json.loads(message)
            newMessage = msg['message'].replace('\n', '\n\n')
            teams_payload = {
                "text": f"**{msg['title'].strip()}**\n\n{newMessage}"
            }
            response = requests.post(TEAMS_WEBHOOK_URL, json=teams_payload)
            response.raise_for_status()
            logger.info(f"Message forwarded successfully: {msg['title']}")
            return
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            time.sleep(retry_delay)
            retry_delay *= 2  # Double the delay for the next attempt
            retry_delay += random.uniform(0, 1)  # Add jitter

    raise Exception("Maximum retry attempts reached")


def on_message(ws, message):
    logger.info(f"on_message {message}")
    on_message_fetch_with_backoff(message)


def on_error(ws, error):
    logger.error(f"WebSocket error: {str(error)}")


def on_close(ws, close_status_code, close_msg):
    logger.info("WebSocket connection closed")


def on_open(ws):
    logger.info("WebSocket connection established")


if __name__ == "__main__":
    ws = websocket.WebSocketApp(
        GOTIFY_WS_URL,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
        on_open=on_open
    )
    ws.run_forever()
