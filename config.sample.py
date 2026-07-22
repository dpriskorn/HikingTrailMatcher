import logging

user_name = ""
bot_password = ""  # nosec
user_name_only = "input your user name here"

loglevel = logging.INFO
debug_json = False
validate_before_upload = True
upload_to_wikidata = True
request_timeout = 10
user_agent = (
    f"hiking_trail_matcher, "
    f"see https://github.com/dpriskorn/hiking_trail_matcher/ "
    f"User:{user_name_only}"
)

language_code = "sv"
country_qid = "Q34"

max_days_between_new_check: int = int(365 * 0.5)
min_similarity: float = 0.8
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
