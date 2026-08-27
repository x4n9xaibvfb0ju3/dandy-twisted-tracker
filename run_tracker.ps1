$ErrorActionPreference = "Stop"

# ALL notifies whenever the featured Twisted changes.
$env:TARGET_TWISTED = "ALL"

if (-not $env:DISCORD_WEBHOOK) {
    $env:DISCORD_WEBHOOK = Read-Host "Paste your regenerated Discord webhook URL"
}

# Enter the numeric Discord user ID to receive an actual mention, or leave blank.
if (-not $env:DISCORD_MENTION) {
    $discordUserId = Read-Host "Enter your Discord user ID for a ping (or press Enter to skip)"
    if ($discordUserId) {
        $env:DISCORD_MENTION = "<@$discordUserId>"
    }
}

python "$PSScriptRoot\twisted_tracker.py"
