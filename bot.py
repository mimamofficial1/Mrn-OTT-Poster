import os
import html
import logging
from urllib.parse import quote_plus

from dotenv import load_dotenv
from curl_cffi import requests
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN") or os.getenv("TELEGRAM_BOT_TOKEN")
API_TOKEN = os.getenv("API_TOKEN")
API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")

CC_HANDLE = os.getenv("CC_HANDLE", "@Mrn_Officialx")

# Friendly display name shown as "<Label> Poster: <link>", keyed by API endpoint
# so every alias of a service (amz/amazon, mx/mxplayer, etc.) shares one label.
SERVICE_LABELS = {
    "/posters/aaonxt": "AaoNxt",
    "/posters/addatimes": "Addatimes",
    "/posters/aha": "Aha",
    "/posters/airtel": "Airtelxstream",
    "/posters/amazon": "Amazon Prime",
    "/posters/apple": "Apple TV",
    "/posters/atrangii": "Atrangii",
    "/posters/bms": "BookMyShow",
    "/posters/chaupal": "Chaupal",
    "/posters/crunchyroll": "Crunchyroll",
    "/posters/dangal": "Dangal Play",
    "/posters/erosnow": "Eros Now",
    "/posters/hoichoi": "Hoichoi",
    "/posters/hulu": "Hulu",
    "/posters/hungama": "Hungama",
    "/posters/iqyi": "iQIYI",
    "/posters/jojo": "Jojo",
    "/posters/lionsgate": "Lionsgate Play",
    "/posters/mubi": "Mubi",
    "/posters/mxplayer": "MX Player",
    "/posters/nf": "Netflix",
    "/posters/nf/episode": "Netflix",
    "/posters/plex": "Plex",
    "/posters/playflix": "Playflix",
    "/posters/sainaplay": "SainaPlay",
    "/posters/shemaroo": "ShemarooMe",
    "/posters/sonyliv": "Sonyliv",
    "/posters/sunnxt": "SunNXT",
    "/posters/tataplay": "Tata Play Binge",
    "/posters/ticketnew": "TicketNew",
    "/posters/tubi": "Tubi",
    "/posters/ultra": "Ultra",
    "/posters/ultrajhakaas": "UltraJhakaas",
    "/posters/viki": "Viki",
    "/posters/viu": "Viu",
    "/posters/viva": "Vivamax",
    "/posters/wetv": "WeTV",
    "/posters/youku": "Youku",
    "/posters/youtube": "YouTube",
    "/posters/zee5": "Zee5",
    "/posters/jiohotstar": "JioHotstar",
    "/posters/jiohotstar/episode": "JioHotstar",
}

# The field shown as a raw, full link on the "<Label> Poster:" line.
PRIMARY_FIELD_ORDER = ["landscape", "cover", "portrait", "still", "poster", "banner", "thumbnail", "image"]

# Every other field present gets shown as a compact "<Field>: Link" hyperlink,
# in this order.
SECONDARY_FIELD_ORDER = ["portrait", "banner", "cover", "logo", "square", "still", "poster", "thumbnail", "backdrop"]

SERVICES = {
    "aaonxt": "/posters/aaonxt",
    "addatimes": "/posters/addatimes",
    "aha": "/posters/aha",
    "airtel": "/posters/airtel",
    "amazon": "/posters/amazon",
    "amz": "/posters/amazon",
    "apple": "/posters/apple",
    "appletv": "/posters/apple",
    "atrangii": "/posters/atrangii",
    "bms": "/posters/bms",
    "bookmyshow": "/posters/bms",
    "chaupal": "/posters/chaupal",
    "crunchyroll": "/posters/crunchyroll",
    "dangal": "/posters/dangal",
    "erosnow": "/posters/erosnow",
    "eros": "/posters/erosnow",
    "hoichoi": "/posters/hoichoi",
    "hulu": "/posters/hulu",
    "hungama": "/posters/hungama",
    "iqyi": "/posters/iqyi",
    "jojo": "/posters/jojo",
    "lionsgate": "/posters/lionsgate",
    "mubi": "/posters/mubi",
    "mxplayer": "/posters/mxplayer",
    "mx": "/posters/mxplayer",
    "netflix": "/posters/nf",
    "nf": "/posters/nf",
    "netflixep": "/posters/nf/episode",
    "nfep": "/posters/nf/episode",
    "episode": "/posters/nf/episode",
    "plex": "/posters/plex",
    "plextv": "/posters/plex",
    "playflix": "/posters/playflix",
    "sainaplay": "/posters/sainaplay",
    "shemaroo": "/posters/shemaroo",
    "sonyliv": "/posters/sonyliv",
    "sunnxt": "/posters/sunnxt",
    "tataplay": "/posters/tataplay",
    "ticketnew": "/posters/ticketnew",
    "tubi": "/posters/tubi",
    "ultra": "/posters/ultra",
    "ultrajhakaas": "/posters/ultrajhakaas",
    "viki": "/posters/viki",
    "viu": "/posters/viu",
    "viva": "/posters/viva",
    "vivamax": "/posters/viva",
    "wetv": "/posters/wetv",
    "youku": "/posters/youku",
    "youtube": "/posters/youtube",
    "yt": "/posters/youtube",
    "zee5": "/posters/zee5",
    "jiohotstar": "/posters/jiohotstar",
    "hotstar": "/posters/jiohotstar",
    "jhs": "/posters/jiohotstar",
    "jiohotstarep": "/posters/jiohotstar/episode",
    "hotstarep": "/posters/jiohotstar/episode",
    "jhsep": "/posters/jiohotstar/episode",
}

DOMAIN_SERVICE_HINTS = {
    "aaonxt.com": "aaonxt",
    "addatimes.com": "addatimes",
    "aha.video": "aha",
    "airtelxstream.in": "airtel",
    "primevideo.com": "amazon",
    "amazon.com": "amazon",
    "tv.apple.com": "apple",
    "atrangii.in": "atrangii",
    "bookmyshow.com": "bms",
    "chaupal.tv": "chaupal",
    "crunchyroll.com": "crunchyroll",
    "dangalplay.com": "dangal",
    "erosnow.com": "erosnow",
    "hoichoi.tv": "hoichoi",
    "hulu.com": "hulu",
    "hungama.com": "hungama",
    "iq.com": "iqyi",
    "jojoapp.in": "jojo",
    "lionsgateplay.com": "lionsgate",
    "mubi.com": "mubi",
    "mxplayer.in": "mxplayer",
    "netflix.com": "netflix",
    "plex.tv": "plex",
    "playflix.app": "playflix",
    "sainaplay.com": "sainaplay",
    "shemaroome.com": "shemaroo",
    "sonyliv.com": "sonyliv",
    "sunnxt.com": "sunnxt",
    "tataplaybinge.com": "tataplay",
    "ticketnew.com": "ticketnew",
    "tubitv.com": "tubi",
    "ultrajhakaas.com": "ultrajhakaas",
    "ultraindia.com": "ultra",
    "viki.com": "viki",
    "viu.com": "viu",
    "vivamax.net": "vivamax",
    "wetv.vip": "wetv",
    "youku.tv": "youku",
    "youtube.com": "youtube",
    "youtu.be": "youtube",
    "zee5.com": "zee5",
    "hotstar.com": "jiohotstar",
}

HELP_TEXT = """
<b>🎬 AnimeCall Posters Telegram Bot</b>

Send:
<code>/poster service url</code>

Example:
<code>/poster aaonxt https://aaonxt.com/movies/example-slug</code>

You can also use direct commands:
<code>/aaonxt https://aaonxt.com/...</code>
<code>/netflix 81215567</code>
<code>/nfep https://www.netflix.com/watch/81214042</code>
<code>/nfep 81214042</code>
<code>/jiohotstar https://www.hotstar.com/in/movies/example/1000091195</code>
<code>/jhsep 1000282843</code>
<code>/youtube https://youtu.be/...</code>

Or send only a supported OTT URL and I will try to auto-detect the service.

Use <code>/services</code> to see all services.
""".strip()


def esc(value):
    return html.escape(str(value))


def detect_service(text: str):
    low = text.lower()
    for domain, service in DOMAIN_SERVICE_HINTS.items():
        if domain in low:
            return service
    return None


def build_api_url(service: str, content_url: str):
    endpoint = SERVICES[service]
    return f"{API_BASE_URL}{endpoint}?url={quote_plus(content_url)}"


def fetch_poster(service: str, content_url: str):
    if service not in SERVICES:
        raise ValueError(f"Unsupported service: {service}")

    headers = {}
    if API_TOKEN:
        headers["Authorization"] = f"Bearer {API_TOKEN}"

    response = requests.get(build_api_url(service, content_url), headers=headers, timeout=60)
    try:
        data = response.json()
    except Exception:
        data = {"error": response.text[:1000]}

    if response.status_code >= 400:
        short = data.get("error") or data.get("detail") or f"API error {response.status_code}"
        extra = data.get("details") or data.get("raw")
        if extra:
            short = f"{short} | {str(extra)[:300]}"
        raise RuntimeError(short)
    return data


def format_result(service: str, data: dict):
    title = data.get("title") or data.get("name") or data.get("movie") or "Poster result"
    label = SERVICE_LABELS.get(SERVICES.get(service, ""), service.title())

    primary_key = next((k for k in PRIMARY_FIELD_ORDER if data.get(k)), None)
    primary_url = data.get(primary_key) if primary_key else None

    lines = [f"{esc(label)} Poster: {esc(primary_url) if primary_url else 'N/A'}", ""]

    for key in SECONDARY_FIELD_ORDER:
        if key == primary_key:
            continue
        value = data.get(key)
        if value:
            lines.append(f'{esc(key.title())}: <a href="{esc(value)}">Link</a>')

    lines.append("")
    lines.append(esc(title))
    lines.append("")
    lines.append(f"<blockquote>cc: {esc(CC_HANDLE)}</blockquote>")

    return "\n".join(lines), primary_url


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(HELP_TEXT, parse_mode=ParseMode.HTML, disable_web_page_preview=True)


async def services(update: Update, context: ContextTypes.DEFAULT_TYPE):
    unique = sorted(set(SERVICES.keys()))
    chunks = []
    line = ""
    for name in unique:
        item = f"/{name} "
        if len(line) + len(item) > 80:
            chunks.append(line.rstrip())
            line = ""
        line += item
    if line:
        chunks.append(line.rstrip())

    text = "<b>Supported services</b>\n\n" + "\n".join(f"<code>{esc(c)}</code>" for c in chunks)
    await update.effective_message.reply_text(text, parse_mode=ParseMode.HTML, disable_web_page_preview=True)


async def poster(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.effective_message.reply_text(
            "Use: <code>/poster service url</code>\nExample: <code>/poster zee5 https://...</code>",
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
        )
        return

    service = context.args[0].lower().strip()
    content_url = " ".join(context.args[1:]).strip()
    await send_poster(update, service, content_url)


async def command_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # MessageHandler does not fill context.args. Parse the command text manually.
    text = update.effective_message.text or ""
    parts = text.split(maxsplit=1)
    command = parts[0].split("@")[0].lstrip("/").lower() if parts else ""
    arg_text = parts[1].strip() if len(parts) > 1 else ""

    if command in {"start", "help"}:
        await start(update, context)
        return
    if command == "services":
        await services(update, context)
        return
    if command == "poster":
        if not arg_text:
            await update.effective_message.reply_text(
                "Use: <code>/poster service url</code>",
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True,
            )
            return
        poster_parts = arg_text.split(maxsplit=1)
        if len(poster_parts) < 2:
            await update.effective_message.reply_text(
                "Use: <code>/poster service url</code>",
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True,
            )
            return
        await send_poster(update, poster_parts[0].lower(), poster_parts[1].strip())
        return

    service = command
    if service not in SERVICES:
        await update.effective_message.reply_text("Unknown command. Use /services or /poster service url")
        return
    if not arg_text:
        await update.effective_message.reply_text(
            f"Use: <code>/{esc(service)} url</code>",
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
        )
        return
    await send_poster(update, service, arg_text)


async def auto_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.effective_message.text.strip()
    service = detect_service(text)
    if not service:
        await update.effective_message.reply_text(
            "I could not auto-detect this URL. Use <code>/poster service url</code>.",
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
        )
        return
    await send_poster(update, service, text)


async def send_poster(update: Update, service: str, content_url: str):
    service = service.lower().strip()
    msg = await update.effective_message.reply_text("Fetching poster...")
    try:
        data = fetch_poster(service, content_url)
        text, primary_url = format_result(service, data)

        await msg.edit_text(text, parse_mode=ParseMode.HTML, disable_web_page_preview=True)

        if primary_url:
            try:
                await update.effective_message.reply_photo(photo=primary_url)
            except Exception:
                # Some providers return URLs Telegram itself cannot fetch;
                # the text message above still has the working link.
                pass
    except Exception as exc:
        await msg.edit_text(f"❌ Error: <code>{esc(exc)}</code>", parse_mode=ParseMode.HTML, disable_web_page_preview=True)


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is missing. Add BOT_TOKEN=your_telegram_bot_token to .env")
    if not API_TOKEN:
        logging.warning("API_TOKEN is missing. Protected API routes may return 401.")

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", start))
    app.add_handler(CommandHandler("services", services))
    app.add_handler(CommandHandler("poster", poster))
    app.add_handler(MessageHandler(filters.COMMAND, command_router))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, auto_url))

    print("Telegram bot running with polling...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
