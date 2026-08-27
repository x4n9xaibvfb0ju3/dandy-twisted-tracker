#!/usr/bin/env python3
"""Dandy's World Daily Twisted Board tracker.

Polls the Miraheze wiki for the current Daily Twisted Board and posts a
Discord webhook when the featured Twisted matches your target(s).

Configure via environment variables (set in the GitHub workflow):
    TARGET_TWISTED   - a specific Twisted name, a comma-separated list of names,
                       or "ALL" to be pinged for every Twisted that goes on the board.
                       Matching is case-insensitive and ignores the word "Twisted".
    DISCORD_WEBHOOK  - your Discord webhook URL.
    DISCORD_MENTION  - optional. Text to prefix the message, e.g. "<@&123456789>" or
                       "<@123456789>" to actually ping you. Defaults to no mention.
"""

import os
import re
import sys
import html
import urllib.request
import json

WIKI_URL = "https://dandysworld.miraheze.org/wiki/Daily_Twisted_Board"
STATE_FILE = "last_notified.txt"

# Names of Twisteds that can appear on the board, for reference/validation.
KNOWN_TWISTEDS = [
    "Poppy", "Boxten", "Cosmo", "Toodles", "Rodger", "Scraps", "Tisha",
    "Shrimpo", "Finn", "Goob", "Glisten", "Flutter", "Sprout", "Brightney",
    "Dandy", "Shelly", "Pebble", "Astro", "Vee", "Razzle & Dazzle",
    "Gigi", "Connie", "Teagan", "Looey", "Ginger", "Coal", "Bobette", "Rudie",
    "Twisted Yatta", "Yatta",
]


def fetch_wiki_page() -> str:
    req = urllib.request.Request(WIKI_URL, headers={"User-Agent": "dandy-twisted-tracker/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="replace")


def parse_featured(page: str):
    """Return (twisted_name, until_text) or None if not found."""
    # Strip HTML tags/entities so we can read the sentence as plain text:
    #   Twisted Razzle & Dazzle is more likely to spawn until August 25th, 7:00 PM EST.
    text = re.sub(r"<[^>]+>", " ", page)
    text = html.unescape(text)
    m = re.search(
        r"Twisted\s+(.+?)\s+is more likely to spawn until\s+([^.,]+)",
        text,
        re.IGNORECASE,
    )
    if not m:
        return None
    name = re.sub(r"\s+", " ", m.group(1)).strip()
    until = re.sub(r"\s+", " ", m.group(2)).strip()
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


def main() -> None:
    target = os.environ.get("TARGET_TWISTED", "ALL")
    webhook = os.environ.get("DISCORD_WEBHOOK", "")
    mention = os.environ.get("DISCORD_MENTION", "")

    if not webhook:
        print("ERROR: DISCORD_WEBHOOK not set")
        sys.exit(1)

    try:
        page = fetch_wiki_page()
    except Exception as e:
        print(f"WARN: failed to fetch wiki page: {e}")
        sys.exit(0)

    parsed = parse_featured(page)
    if not parsed:
        print("WARN: could not parse the current Twisted from the wiki page")
        sys.exit(0)

    twisted_name, until = parsed
    print(f"Current board: Twisted {twisted_name} until {until}")

    if not matches_target(twisted_name, target):
        print(f"Target is {target!r}; no match. No webhook sent.")
        return

    # Key on Twisted + expiry date so we only ping once per 24h window even
    # if the workflow runs multiple times during the day.
    key = f"{normalize(twisted_name)}|{until}".lower()
    if key == load_last_notified():
        print("Already notified for this Twisted/window. Skipping.")
        return

    prefix = f"{mention} " if mention else ""
    content = (
        f"{prefix}**Twisted {twisted_name}** is now on the Daily Twisted Board "
        f"and more likely to spawn! Active until **{until}**."
    )

    try:
        post_webhook(webhook, content)
    except Exception as e:
        print(f"ERROR: failed to post webhook: {e}")
        sys.exit(1)

    save_last_notified(key)
    print(f"Webhook sent for Twisted {twisted_name}.")


if __name__ == "__main__":
    main()