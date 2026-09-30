import json
import requests
from config import GH_GIST_TOKEN, GIST_ID

GIST_FILENAME = "state.json"
GIST_API = f"https://api.github.com/gists/{GIST_ID}"
HEADERS = {
    "Authorization": f"Bearer {GH_GIST_TOKEN}",
    "Accept": "application/vnd.github+json",
}


def load_state() -> dict:
    """从 Gist 读取状态。"""
    resp = requests.get(GIST_API, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    content = resp.json()["files"][GIST_FILENAME]["content"]
    return json.loads(content) if content.strip() else {}


def save_state(state: dict) -> None:
    """写回 Gist。"""
    payload = {
        "files": {
            GIST_FILENAME: {
                "content": json.dumps(state, ensure_ascii=False, indent=2)
            }
        }
    }
    resp = requests.patch(GIST_API, headers=HEADERS, json=payload, timeout=15)
    resp.raise_for_status()