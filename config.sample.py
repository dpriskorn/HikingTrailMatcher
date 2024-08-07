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
language_code = "en"
country_qid = "Q34"

# we check once a year for new relations in OSM to avoid
# clogging wikidata with novalue statements
max_days_between_new_check = 365
