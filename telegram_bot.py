import time
import requests
from config import TELEGRAM_BOT_TOKEN

TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"


def send_message(chat_id: int | str, text: str) -> bool:
    url = f"{TELEGRAM_API}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    try:
        resp = requests.post(url, json=payload, timeout=10)
        if resp.status_code == 403:
            # 用户屏蔽了 bot，返回 False 让调用方移除
            return False
        resp.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        print(f"[Telegram] 发送给 {chat_id} 失败: {e}")
        return False


def get_updates(offset: int | None = None) -> list[dict]:
    url = f"{TELEGRAM_API}/getUpdates"
    params = {"timeout": 0, "allowed_updates": ["message"]}
    if offset is not None:
        params["offset"] = offset
    try:
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        return resp.json().get("result", [])
    except requests.exceptions.RequestException as e:
        print(f"[Telegram] getUpdates 失败: {e}")
        return []


HELP_TEXT = (
    "🤖 <b>推特监控机器人</b>\n\n"
    "命令列表：\n"
    "/start - 订阅推文通知\n"
    "/stop - 取消订阅\n"
    "/list - 查看当前监控的账号\n"
    "/status - 查看订阅状态\n"
    "/help - 显示此帮助"
)


def process_updates(offset, subscribers):
    updates = get_updates(offset)
    if not updates:
        return offset, subscribers, []  # 如果 Telegram 没有新消息，直接返回

    subscribers = list(subscribers)
    newly_subscribed = []
    last_update_id = offset

    for upd in updates:
        last_update_id = upd["update_id"] + 1  # 极其重要：更新已读取的 ID，避免重复读取
        msg = upd.get("message")
        if not msg or "text" not in msg:
            continue

        chat_id = msg["chat"]["id"]
        text = msg["text"].strip().lower()

        if text.startswith("/start"):
            if chat_id not in subscribers:
                subscribers.append(chat_id)
                newly_subscribed.append(chat_id)
                send_message(
                    chat_id,
                    "✅ 订阅成功！\n\n"
                    "当监控的账号发布新推文时，你会第一时间收到通知。\n"
                    "发送 /stop 可随时取消订阅。",
                )
            else:
                send_message(chat_id, "你已经订阅过了。发送 /status 查看状态。")

        elif text.startswith("/stop"):
            if chat_id in subscribers:
                subscribers.remove(chat_id)
                send_message(chat_id, "👋 已取消订阅。发送 /start 可重新订阅。")
            else:
                send_message(chat_id, "你还没有订阅。发送 /start 订阅。")

        elif text.startswith("/list"):
            from config import TWITTER_ACCOUNTS
            accounts = "\n".join(f"• @{a}" for a in TWITTER_ACCOUNTS)
            send_message(chat_id, f"📋 <b>当前监控账号：</b>\n{accounts}")

        elif text.startswith("/status"):
            status = "✅ 已订阅" if chat_id in subscribers else "❌ 未订阅"
            send_message(
                chat_id,
                f"你的状态：{status}\n当前总订阅人数：{len(subscribers)}",
            )

        elif text.startswith("/help") or text.startswith("/"):
            send_message(chat_id, HELP_TEXT)

        time.sleep(0.1)  # 避免触发 Telegram 限速

    return last_update_id, subscribers, newly_subscribed


def format_tweet(username: str, tweet: dict) -> str:
    text = tweet.get("full_text", tweet.get("text", ""))
    tweet_id = tweet.get("id", "")
    if len(text) > 800:
        text = text[:800] + "..."
    return (
        f"🐦 <b>@{username}</b> 发布了新推文\n\n"
        f"{text}\n\n"
        f"🔗 <a href='https://x.com/{username}/status/{tweet_id}'>查看原文</a>"
    )
