import os
import threading
import time

from dotenv import load_dotenv
import uvicorn

load_dotenv()


def start_api():
    host = os.getenv("API_HOST", "127.0.0.1")
    port = int(os.getenv("API_PORT", "8000"))
    uvicorn.run("main:app", host=host, port=port, log_level="info")


if __name__ == "__main__":
    # Start FastAPI locally so the Telegram bot can call the existing poster API.
    api_thread = threading.Thread(target=start_api, daemon=True)
    api_thread.start()
    time.sleep(2)

    from bot import main as start_bot

    start_bot()
