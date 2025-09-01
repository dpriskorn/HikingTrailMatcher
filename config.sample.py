import logging

loglevel = logging.INFO
validate_before_upload = True
upload_to_wikidata = True
request_timeout = 10
user_name = ""
bot_password = ""  # nosec
user_name_only = "input your user name here"
user_agent = (
    f"hiking_trail_matcher, "
    f"see https://github.com/dpriskorn/"
    f"hiking_trail_matcher/ User:{user_name_only}"
)

# This controls which hiking trails to fetch and work on
# this is used to know if a label exist for the language of the country
# language_code = "en"
language_code = "sv"
# country_qid = "Q30" # USA
country_qid = "Q34"

# we check rather seldom for new relations in OSM
max_days_between_new_check: int = int(365 * 0.5)
# levenstein distance
min_similarity: float = 0.8
# They should be lowercase
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
