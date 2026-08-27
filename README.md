# Dandy's World Twisted Tracker

Polls the Miraheze wiki's Daily Twisted Board page every hour and posts a
Discord webhook when your target Twisted is on the board (i.e. more likely
to spawn for the next 24 hours).

## Setup

1. Push this repo to GitHub (or use GitHub Desktop to publish it).
2. Create a Discord webhook:
   - Channel settings → Integrations → Webhooks → New Webhook
   - Copy the webhook URL.
3. Add a repository **Secret** named `DISCORD_WEBHOOK` with that URL:
   Repo → Settings → Secrets and variables → Actions → New repository secret.
4. Add a repository **Variable** named `TARGET_TWISTED`:
   - `ALL` → ping for every Twisted that appears on the board.
   - `Shelly` or `Finn` → ping only for that one.
   - `Finn, Shelly, Pebble` → ping for any of these.
   (Variables live under the same page, "Variables" tab.)
5. (Optional) Add a repository **Variable** named `DISCORD_MENTION` if you
   want to actually ping yourself or a role, e.g. `<@123456789>` or `<@&987654321>`.

The workflow runs every hour on the hour (UTC). If your target Twisted
appears on the board, you get a ping. You'll only get pinged once per
24h window for the same Twisted.

## Manual run

Open the Actions tab → select the workflow → "Run workflow".

## Files

- `twisted_tracker.py` – the poller
- `.github/workflows/twisted-tracker.yml` – the hourly cron job