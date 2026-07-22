import logging
from os import getenv

from dotenv import load_dotenv

load_dotenv()

user_name = getenv("USER_NAME", "")
bot_password = getenv("BOT_PASSWORD", "")

if not user_name or not bot_password:
    raise ValueError("USER_NAME and BOT_PASSWORD must be set in .env")
user_name_only = getenv("USER_NAME_ONLY", "input your user name here")

loglevel = getattr(logging, getenv("LOGLEVEL", "INFO"))
debug_json = getenv("DEBUG_JSON", "false").lower() == "true"
validate_before_upload = getenv("VALIDATE_BEFORE_UPLOAD", "true").lower() == "true"
upload_to_wikidata = getenv("UPLOAD_TO_WIKIDATA", "true").lower() == "true"
request_timeout = int(getenv("REQUEST_TIMEOUT", "10"))
user_agent = (
    f"hiking_trail_matcher, "
    f"see https://github.com/dpriskorn/hiking_trail_matcher/ "
    f"User:{user_name_only}"
)

language_code = getenv("LANGUAGE_CODE", "sv")
country_qid = getenv("COUNTRY_QID", "Q34")

max_days_between_new_check: int = int(getenv("MAX_DAYS_BETWEEN_NEW_CHECK", "182"))
min_similarity: float = float(getenv("MIN_SIMILARITY", "0.8"))

EXCLUDED_TERM_WORDS = {
    "roundtrip",
    "rundslinga",
    "trail",
    "vandringsled",
    "led",
    "vandringsförslag",
    "runt",
    "i",
    "vandring",
    "hälsans",
    "stig",
    "signaturled",
    "skogsstigen",
    "naturreservat",
    "slingan",
    "naturstig",
    "etapp",
}
