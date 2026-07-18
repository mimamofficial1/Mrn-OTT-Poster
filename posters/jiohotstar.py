import os
import re
from curl_cffi import requests
from dotenv import load_dotenv
from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

load_dotenv()

router = APIRouter()

API_URL = "https://api.hotstar.com/o/v1"

# URL path segment -> Hotstar's internal content type name
_TYPE_MAP = {
    "movies": "movie",
    "movie": "movie",
    "sports": "match",
    "clips": "content",
    "episode": "episode",
}


# ---------------- HELPERS ----------------

def extract_hotstar_id_type(value: str, default_type: str = "movie"):
    """Accepts either a raw numeric content/episode ID or a full JioHotstar
    (hotstar.com) URL and returns (content_id, content_type)."""
    value = value.strip()

    if value.isdigit():
        return value, default_type

    ids = re.findall(r"(\d{6,})", value)
    if not ids:
        raise ValueError(
            "Could not extract a JioHotstar content/episode ID. Send either the "
            "numeric ID or a full hotstar.com URL."
        )

    type_match = re.search(r"/(movies|movie|sports|clips|episode|tv|shows)/(.+)", value)

    if not type_match:
        return ids[-1], default_type

    keyword = type_match.group(1)

    if keyword in ("tv", "shows"):
        # .../shows/{slug}/{show-id}                       -> show-level page  (2 segments)
        # .../shows/{slug}/{show-id}/{ep-slug}/{ep-id}...   -> episode page     (4+ segments)
        rest = type_match.group(2).split("?")[0].strip("/")
        segments = [s for s in rest.split("/") if s]
        content_type = "episode" if len(segments) >= 4 else "show"
    else:
        content_type = _TYPE_MAP.get(keyword, default_type)

    # The last long numeric segment in a hotstar.com URL is always the
    # content/episode id being viewed (matches how the site itself links).
    return ids[-1], content_type


def collect_image_urls(obj, found=None):
    """Recursively scan the API response for any string value that looks
    like an image URL, keyed by its original field name."""
    if found is None:
        found = {}

    if isinstance(obj, dict):
        for key, value in obj.items():
            if isinstance(value, str) and value.startswith("http") and any(
                kw in key.lower()
                for kw in ("image", "thumbnail", "poster", "logo", "backdrop", "art")
            ):
                found[key] = value
            else:
                collect_image_urls(value, found)
    elif isinstance(obj, list):
        for entry in obj:
            collect_image_urls(entry, found)

    return found


def map_images(images: dict):
    def pick(*keywords):
        for key, value in images.items():
            low = key.lower()
            if any(kw in low for kw in keywords):
                return value
        return None

    return {
        "portrait": pick("portrait", "poster", "vertical"),
        "landscape": pick("landscape", "horizontal", "wide"),
        "square": pick("square", "1x1"),
        "cover": pick("cover", "hero", "backdrop", "banner"),
        "logo": pick("logo", "title_logo", "titlelogo"),
    }


# ---------------- CORE LOGIC ----------------

def fetch_hotstar_detail(content_id: str, content_type: str = "movie"):
    headers = {
        "x-country-code": "IN",
        "x-platform-code": "PCTV",
        "user-agent": "Mozilla/5.0",
    }

    user_token = os.getenv("HOTSTAR_USER_TOKEN")
    if user_token:
        headers["x-hs-usertoken"] = user_token

    session = requests.Session(impersonate="chrome")

    try:
        res = session.get(
            f"{API_URL}/{content_type}/detail",
            headers=headers,
            params={"tas": 5, "contentId": content_id},
            timeout=20,
        )
    except Exception as e:
        return {"error": "Request failed", "details": str(e)}

    if res.status_code != 200:
        return {"error": f"API failed {res.status_code}", "details": res.text}

    try:
        data = res.json()
    except Exception:
        return {"error": "Invalid JSON from API", "raw": res.text}

    item = (data.get("body", {}) or {}).get("results", {}).get("item", {})
    if not item:
        return {"error": "Content not found for this ID/type", "raw": data}

    title = item.get("title")
    year = item.get("year")

    images = collect_image_urls(item)
    mapped = map_images(images)

    result = {
        "title": f"{title} - ({year})" if year else title,
        "portrait": mapped["portrait"],
        "landscape": mapped["landscape"],
        "square": mapped["square"],
        "cover": mapped["cover"],
        "logo": mapped["logo"],
    }

    if content_type == "episode":
        result["show"] = item.get("showName")
        result["season_number"] = item.get("seasonNo")
        result["episode_number"] = item.get("episodeNo")

    # Keep every raw image URL we found too, in case the standard fields
    # above miss something - useful while we dial in the field mapping.
    result["all_images"] = images

    return result


# ---------------- FASTAPI ROUTES ----------------

@router.get("/jiohotstar")
def jiohotstar_poster(
    url: str = Query(..., description="JioHotstar content URL, or a raw numeric content ID"),
    type: str = Query(None, description="Override content type: movie, episode, match, content"),
):
    try:
        content_id, detected_type = extract_hotstar_id_type(url, default_type="movie")
    except ValueError as e:
        return JSONResponse(content={"error": str(e)}, status_code=400)

    result = fetch_hotstar_detail(content_id, type or detected_type)

    if "error" in result:
        return JSONResponse(content=result, status_code=400)

    return result


@router.get("/jiohotstar/episode")
def jiohotstar_episode(
    url: str = Query(..., description="JioHotstar episode watch URL, or a raw numeric episode ID")
):
    try:
        content_id, _ = extract_hotstar_id_type(url, default_type="episode")
    except ValueError as e:
        return JSONResponse(content={"error": str(e)}, status_code=400)

    result = fetch_hotstar_detail(content_id, "episode")

    if "error" in result:
        return JSONResponse(content=result, status_code=400)

    return result
