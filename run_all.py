import os
import threading
import time

from dotenv import load_dotenv
import uvicorn

load_dotenv()

# Railway injects PORT automatically. Fall back to API_PORT (local dev) then 8000.
API_PORT = int(os.getenv("PORT", os.getenv("API_PORT", "8000")))
# Must bind 0.0.0.0 on Railway, not 127.0.0.1, or the container never becomes reachable.
API_HOST = os.getenv("API_HOST", "0.0.0.0")

# bot.py always calls the API on localhost inside the same container, no matter
# what host we bind for external traffic. Force this so it can never drift out
# of sync with the port uvicorn actually starts on.
os.environ["API_BASE_URL"] = f"http://127.0.0.1:{API_PORT}"


def start_api():
    uvicorn.run("main:app", host=API_HOST, port=API_PORT, log_level="info")


if __name__ == "__main__":
    # Start FastAPI locally so the Telegram bot can call the existing poster API.
    api_thread = threading.Thread(target=start_api, daemon=True)
    api_thread.start()
    time.sleep(2)

    from bot import main as start_bot

    start_bot()
