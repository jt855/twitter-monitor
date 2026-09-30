import sys
import time
from config import TWITTER_ACCOUNTS
from state import load_state, save_state
from sorsa_client import fetch_user_tweets
from telegram_bot import (
    process_updates,
    send_message,
    format_tweet,
    HELP_TEXT,
)


def main():
    state = load_state()
    subscribers = state.get("subscribers", [])
    last_seen = state.get("last_seen_ids", {})
    offset = state.get("update_offset")

    # ===== 1. 处理订阅命令 =====
    offset, subscribers, newly = process_updates(offset, subscribers)

    # 首次有订阅者时，发一条欢迎（可选）
    if newly and not state.get("bootstrapped"):
        for chat_id in newly:
            send_message(
                chat_id,
                "🚀 机器人已就绪，开始为你监控推文。\n\n" + HELP_TEXT,
            )

    # ===== 2. 拉取推文并推送 =====
    total_sent = 0
    failed_chats = []

    for username in TWITTER_ACCOUNTS:
        tweets = fetch_user_tweets(username)
        if not tweets:
            continue

        newest_id = int(tweets[0]["id"])
        prev_id = last_seen.get(username)

        # 首次监控该账号：只建立基线，不推送历史
        if prev_id is None:
            last_seen[username] = newest_id
            print(f"[Monitor] @{username} 基线: {newest_id}")
            continue

        new_tweets = [t for t in tweets if int(t["id"]) > prev_id]
        if not new_tweets:
            continue

        # 从旧到新推送，保证顺序
        for tweet in reversed(new_tweets):
            text = format_tweet(username, tweet)
            for chat_id in subscribers:
                if chat_id in failed_chats:
                    continue
                ok = send_message(chat_id, text)
                if ok:
                    total_sent += 1
                else:
                    failed_chats.append(chat_id)
                time.sleep(0.05)  # 单聊限速约 1 条/秒，这里留足余量
            print(f"[Monitor] @{username} 新推文 {tweet['id']}")

        last_seen[username] = newest_id

    # 清理失效订阅者（已屏蔽 bot 的用户）
    if failed_chats:
        subscribers = [c for c in subscribers if c not in failed_chats]
        print(f"[Monitor] 移除失效订阅者: {failed_chats}")

    # ===== 3. 写回状态 =====
    state.update(
        {
            "subscribers": subscribers,
            "last_seen_ids": last_seen,
            "update_offset": offset,
            "bootstrapped": True,
            "last_run": int(time.time()),
        }
    )
    save_state(state)
    print(f"[Monitor] 完成。订阅者 {len(subscribers)} 人，本轮发送 {total_sent} 条。")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[Fatal] {e}", file=sys.stderr)
        sys.exit(1)