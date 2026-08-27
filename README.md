# Kalvium Daily Journal Bot

Automatically submits the "Simulated Work Daily Journal" Google Form every
weekday at 4:00 PM IST via GitHub Actions, marking "working day, present"
and filling the four follow-up questions with varied generated content.

## How it works

- `daily_fill.py` reuses a saved, logged-in Google session (no password
  ever stored) to open the form and submit it headlessly.
- The session is stored as the `AUTH_STATE` repo secret and restored at the
  start of each workflow run.
- The schedule lives in `.github/workflows/daily-journal.yml`
  (`30 10 * * 1-5` UTC = 4:00 PM IST, Mon-Fri).

## When the session expires ("logged out")

Google Workspace (kalvium.community) can force re-authentication after some
period. When that happens, the scheduled run fails and GitHub emails you a
"workflow run failed" notification, with the log saying the session expired.

To fix it, re-run the one-time login capture and update the secret:

```
venv\Scripts\python.exe discover_form.py
Get-Content -Raw auth_state.json | gh secret set AUTH_STATE --repo Shriraj1901/kalvium-daily-journal-bot
```

`discover_form.py` opens a real browser window — log into
`shriraj.jadhav.s73@kalvium.community`, wait until the form itself is visible,
then press Enter in the terminal. That regenerates `auth_state.json`
locally, which the second command uploads as the new secret.

The default form URL is the Kalvium journal form currently configured in the
scripts. To use a different form, set `FORM_URL` before running either script.

## Manually triggering a run

```
gh workflow run daily-journal.yml --repo Shriraj1901/kalvium-daily-journal-bot
```

## Notes

- Holidays/leave days aren't auto-detected — the bot always marks
  "present". Disable the workflow manually (Actions tab → ... → Disable
  workflow) on days you don't want it to run.
- This repo is private. `auth_state.json` is never committed (see
  `.gitignore`) — it only ever lives as the encrypted `AUTH_STATE` secret.
