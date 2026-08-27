# Dandy's World Twisted Tracker

Polls the Fandom wiki's Daily Twisted Board page and posts a Discord webhook
when the featured Twisted changes. It can run continuously on your computer or
as an hourly GitHub Actions job.

## Setup

1. Create a Discord webhook:
   - Channel settings → Integrations → Webhooks → New Webhook
   - Copy the webhook URL.
2. For GitHub Actions, push this folder to GitHub and add a repository **Secret** named `DISCORD_WEBHOOK` with that URL:
   Repo → Settings → Secrets and variables → Actions → New repository secret.
3. Set `TARGET_TWISTED`:
   - `ALL` → ping for every Twisted that appears on the board.
   - `Shelly` or `Finn` → ping only for that one.
   - `Finn, Shelly, Pebble` → ping for any of these.
   (Variables live under the same page, "Variables" tab.)
4. (Optional) Add `DISCORD_MENTION` if you
   want to actually ping yourself or a role, e.g. `<@123456789>` or `<@&987654321>`.

`ALL` sends a notification whenever the board changes. A specific name, such
as `Finn`, sends only when that Twisted becomes featured. Multiple names can be
comma-separated. Add the mention value as `<@123456789>` to make Discord ping
your account. The tracker remembers the last board in `last_notified.txt`.

## Run locally

From this folder in PowerShell:

```powershell
$env:DISCORD_WEBHOOK = "https://discord.com/api/webhooks/..."
$env:TARGET_TWISTED = "ALL"       # or "Finn"
$env:DISCORD_MENTION = "<@123456789>"
$env:RUN_ONCE = "1"               # useful for testing
python twisted_tracker.py
```

Alternatively, run `run_tracker.ps1`. It sets `ALL`, sends one webhook test when
started, then follows the countdown on the wiki and checks when the board is
due to change. It asks for the webhook and your Discord user ID without saving
either to a file. The user ID is needed for an actual Discord mention.

To run the webhook test and one board check, then exit:

```powershell
$env:RUN_ONCE = "1"
.\run_tracker.ps1
Remove-Item Env:RUN_ONCE
```

If the current board was already recorded in `last_notified.txt`, the test will
not send another notification. Delete that file before testing only if you
need to force a test notification.

For continuous monitoring, omit `RUN_ONCE`; it follows the next-change
countdown published on the wiki instead of using a fixed hourly schedule.

The GitHub Actions workflow checks every five minutes (UTC). Its scheduled
runs require the repository secret and variables above, plus permission to
push the small `last_notified.txt` state file back to the repository. GitHub
Actions does not send the startup test; use the local launcher once to test the
webhook.

## Manual run

Open the Actions tab → select the workflow → "Run workflow".

## Files

- `twisted_tracker.py` – the poller
- `.github/workflows/twisted-tracker.yml` – the hourly cron job
