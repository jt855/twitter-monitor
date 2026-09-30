import time
import requests
from config import SORSA_API_KEY, MAX_TWEETS_PER_FETCH

SORSA_BASE_URL = "https://api.sorsa.io/v3"
HEADERS = {"ApiKey": SORSA_API_KEY, "Content-Type": "application/json"}


def fetch_user_tweets(username: str) -> list[dict]:
    url = f"{SORSA_BASE_URL}/user-tweets"
    payload = {"username": username}

    for attempt in range(3):
        try:
            resp = requests.post(url, headers=HEADERS, json=payload, timeout=15)
            if resp.status_code == 429:
                time.sleep(2 ** attempt)
                continue
            resp.raise_for_status()
            return resp.json().get("tweets", [])[:MAX_TWEETS_PER_FETCH]
        except requests.exceptions.RequestException as e:
            print(f"[Sorsa] @{username} 请求失败 ({attempt+1}/3): {e}")
            if attempt < 2:
                time.sleep(2 ** attempt)
    return []