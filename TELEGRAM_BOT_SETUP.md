# Telegram Bot Setup

This project is originally a FastAPI Posters API. I added Telegram polling support.

## 1. Install requirements

```bash
cd ~/AnimeCall-OTT-Poster-Scraper-main
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 2. Create `.env`

```bash
cp .env.example .env
nano .env
```

Set:

```env
BOT_TOKEN=your_botfather_token
API_TOKEN=any_secret_token_you_choose
API_BASE_URL=http://127.0.0.1:8000
```

`API_HOST` and `API_PORT` are optional and commented out by default - only
uncomment them if you're running this on your own VPS/PC and specifically
want to bind to `127.0.0.1`. Leave them commented out on Railway; it
injects its own `PORT` and needs the server bound to `0.0.0.0`, which
`run_all.py` already does automatically.

`BOT_TOKEN` comes from Telegram @BotFather.
`API_TOKEN` can be any secret string, but it must stay the same for the API and bot.

## 3. Run API + Telegram bot together

```bash
source venv/bin/activate
python run_all.py
```

Now open Telegram and send:

```text
/start
/services
/poster aaonxt https://aaonxt.com/movies/example-slug
```

You can also use direct commands:

```text
/aaonxt https://aaonxt.com/...
/netflix 81215567
/youtube https://youtu.be/...
```

## 4. Keep running after SSH closes

```bash
apt install -y screen
screen -S posterbot
cd ~/AnimeCall-OTT-Poster-Scraper-main
source venv/bin/activate
python run_all.py
```

Detach: `CTRL+A` then `D`

Reopen:

```bash
screen -r posterbot
```

## Alternative: run API and bot separately

Terminal 1:

```bash
source venv/bin/activate
uvicorn main:app --host 127.0.0.1 --port 8000
```

Terminal 2:

```bash
source venv/bin/activate
python bot.py
```
