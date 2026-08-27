#!/usr/bin/env python3
"""Dandy's World Daily Twisted Board tracker.

Polls the Fandom wiki for the current Daily Twisted Board and posts a Discord
webhook when the board changes. Set TARGET_TWISTED to a name to only notify
when that Twisted is featured, or leave it as ALL to notify for every change.

Configure via environment variables (set in the GitHub workflow):
    TARGET_TWISTED   - a specific Twisted name, a comma-separated list of names,
                       or "ALL" to be pinged for every Twisted that goes on the board.
                       Matching is case-insensitive and ignores the word "Twisted".
    DISCORD_WEBHOOK  - your Discord webhook URL.
    DISCORD_MENTION  - optional. Text to prefix the message, e.g. "<@&123456789>" or
                        "<@123456789>" to actually ping you. Defaults to no mention.
    The continuous monitor sleeps until the next change shown by the wiki.
"""

import os
import re
import sys
import html
import urllib.request
import json
import time
from datetime import datetime, timedelta, timezone
from urllib.parse import unquote

WIKI_URL = "https://dandys-world-robloxhorror.fandom.com/wiki/Daily_Twisted_Board"
WIKI_API_URL = "https://dandys-world-robloxhorror.fandom.com/api.php?action=parse&page=Daily_Twisted_Board&prop=text&format=json&formatversion=2"
STATE_FILE = os.environ.get("STATE_FILE", "last_notified.txt")

# Names of Twisteds that can appear on the board, for reference/validation.
KNOWN_TWISTEDS = [
    "Poppy", "Boxten", "Cosmo", "Toodles", "Rodger", "Scraps", "Tisha",
    "Shrimpo", "Finn", "Goob", "Glisten", "Flutter", "Sprout", "Brightney",
    "Dandy", "Shelly", "Pebble", "Astro", "Vee", "Razzle & Dazzle",
    "Gigi", "Connie", "Teagan", "Looey", "Ginger", "Coal", "Bobette", "Rudie",
    "Twisted Yatta", "Yatta",
]


def fetch_wiki_page() -> str:
    headers = {
        "User-Agent": "dandy-twisted-tracker/1.0 (personal notifier)",
        "Accept": "text/html,application/xhtml+xml,application/json",
    }
    try:
        req = urllib.request.Request(WIKI_URL, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError:
        # Fandom may reject the article route while still allowing its API.
        req = urllib.request.Request(WIKI_API_URL, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="replace"))
        return data["parse"]["text"]


def parse_featured(page: str):
    """Return (twisted_name, next_change_text) from the Fandom page."""
    # The live page identifies the board with a Twisted_* wiki link. Limit the
    # search to the paragraph after "Currently" so gallery links are ignored.
    current = re.search(r"currently.{0,5000}", page, re.IGNORECASE | re.DOTALL)
    if not current:
        return None

    section = current.group(0)
    link = re.search(r'href=["\']/wiki/(Twisted_[^"\'?#]+)', section, re.IGNORECASE)
    if not link:
        return None

    slug = unquote(link.group(1))
    name = re.sub(r"^Twisted_", "", slug, flags=re.IGNORECASE).replace("_", " ")
    name = html.unescape(re.sub(r"\s+", " ", name)).strip()

    clean_section = html.unescape(re.sub(r"<[^>]+>", " ", section))
    clean_section = " ".join(clean_section.split())
    until_match = re.search(r"It will be\s+(.+?)\s+until", clean_section, re.IGNORECASE)
    until = " ".join(until_match.group(1).split()) if until_match else "the next daily reset"
    return name, until


def normalize(name: str) -> str:
    return re.sub(r"\s+", " ", name.strip().lower()).replace("twisted ", "")


def matches_target(twisted_name: str, target: str) -> bool:
    target = normalize(target)
    if target == "all":
        return True
    twisted = normalize(twisted_name)
    for part in target.split(","):
        part = part.strip()
        if part and (part == twisted or twisted == part or part in twisted or twisted in part):
            return True
    return False


def load_last_notified() -> str:
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    except OSError:
        return ""


def save_last_notified(key: str) -> None:
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        f.write(key)


def post_webhook(webhook_url: str, content: str) -> None:
    payload = json.dumps({"content": content}).encode("utf-8")
    req = urllib.request.Request(
        webhook_url,
        data=payload,
        headers={"Content-Type": "application/json", "User-Agent": "dandy-twisted-tracker/1.0"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        if resp.status not in (200, 204):
            raise RuntimeError(f"webhook returned HTTP {resp.status}")


def seconds_until_change(until: str) -> float | None:
    """Return seconds until the last UTC timestamp in the countdown text."""
    dates = re.findall(
        r"(?:January|February|March|April|May|June|July|August|September|October|November|December)"
        r"\s+\d{1,2}\s+\d{4}\s+\d{1,2}:\d{2}\s+UTC",
        until,
    )
    if not dates:
        return None
    change = datetime.strptime(dates[-1], "%B %d %Y %H:%M UTC").replace(tzinfo=timezone.utc)
    return (change - datetime.now(timezone.utc)).total_seconds()


def main() -> None:
    target = os.environ.get("TARGET_TWISTED", "ALL")
    webhook = os.environ.get("DISCORD_WEBHOOK", "")
    mention = os.environ.get("DISCORD_MENTION", "")

    if not webhook:
        print("ERROR: DISCORD_WEBHOOK not set")
        sys.exit(1)

    once = os.environ.get("RUN_ONCE", "0").lower() in ("1", "true", "yes")

    if os.environ.get("SEND_TEST", "1").lower() in ("1", "true", "yes"):
        try:
            prefix = f"{mention} " if mention else ""
            post_webhook(webhook, f"{prefix}Dandy's World Twisted tracker is online and the webhook is working.")
            print("Webhook test sent successfully.")
        except Exception as e:
            print(f"ERROR: webhook test failed: {e}")
            sys.exit(1)

    while True:
        try:
            page = fetch_wiki_page()
            parsed = parse_featured(page)
            if not parsed:
                raise RuntimeError("could not parse the current Twisted")
            twisted_name, until = parsed
            print(f"Current board: Twisted {twisted_name}; changes {until}")

            key = normalize(twisted_name)
            previous = load_last_notified()
            if key != previous and matches_target(twisted_name, target):
                prefix = f"{mention} " if mention else ""
                content = (
                    f"{prefix}**Twisted {twisted_name}** is now on the Daily Twisted Board "
                    f"and more likely to spawn! The board changes **{until}**."
                )
                post_webhook(webhook, content)
                save_last_notified(key)
                print(f"Webhook sent for Twisted {twisted_name}.")
            elif key == previous:
                print("No board change; skipping webhook.")
            else:
                print(f"Target is {target!r}; change does not match. No webhook sent.")
                # Remember the board so a named target does not notify repeatedly
                # during the same daily window.
                save_last_notified(key)
        except Exception as e:
            print(f"WARN: {e}")

        if once:
            return

        delay = seconds_until_change(until)
        if delay is None:
            print("Countdown could not be read; checking again in 60 seconds.")
            time.sleep(60)
        else:
            # Wake at the displayed reset time. A short retry loop handles
            # wiki caching or a reset that occurs a few seconds late.
            sleep_for = max(1, delay)
            print(f"Next board check in {sleep_for:.0f} seconds.")
            time.sleep(sleep_for)


if __name__ == "__main__":
    main()
