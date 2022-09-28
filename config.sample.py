import logging

loglevel = logging.INFO
upload_to_wikidata = False
user_name = ""
bot_password = ""  # nosec
user_name_only = "input your user name here"
user_agent = f"hiking_trail_matcher, see https://github.com/dpriskorn/hiking_trail_matcher/ User:{user_name_only}"

# This controls which hiking trails to fetch and work on
language_code = "en"
country_qid = "Q30"

# we check once a year for new relations in OSM to avoid
# clogging wikidata with novalue statements
max_days_between_new_check = 365
