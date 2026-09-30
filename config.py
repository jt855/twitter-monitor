import os

SORSA_API_KEY = os.environ["SORSA_API_KEY"]
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
GH_GIST_TOKEN = os.environ["GH_GIST_TOKEN"]
GIST_ID = os.environ["GIST_ID"]

TWITTER_ACCOUNTS = [
    a.strip() for a in os.environ.get("TWITTER_ACCOUNTS", "").split(",") if a.strip()
]
MAX_TWEETS_PER_FETCH = int(os.environ.get("MAX_TWEETS_PER_FETCH", "10"))