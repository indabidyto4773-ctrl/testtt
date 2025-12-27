# Telegram Episode Uploader (Telethon)

This project watches a folder for new episode files and uploads them to a Telegram channel using a user account (Telethon). This supports large file uploads which the Bot API may limit.

## Features
- Monitors a local folder for new files (watch folder)
- Automatically uploads allowed file types to a target Telegram channel
- Moves uploaded files to an `uploaded` folder (or deletes them)
- Shows upload progress in logs

## Important notes
- You must have a Telegram API ID and API HASH from https://my.telegram.org.
- The account you use to authorize the Telethon client must be allowed to post to the target channel (add as admin or allow posting).
- Do NOT use this script to distribute copyrighted content without permission.

## Quick start
1. Clone or copy files to a folder.
2. Copy `config.example.py` -> `config.py` and fill in values (API_ID, API_HASH, TARGET_CHANNEL, etc).
3. Create watch/upload folders if necessary:
   ```
   mkdir watch uploaded
   ```
4. Install dependencies:
   ```
   python3 -m pip install -r requirements.txt
   ```
5. Run:
   ```
   python bot.py
   ```
   On first run Telethon will ask for your phone number and confirmation code to create a session file.

6. Add files to the `watch` folder. When new files appear they will be uploaded automatically.

## Running in background / Docker
You can run with systemd or Docker. A sample Dockerfile is provided.

## Bot API alternative
If your episodes are small (<50 MB) and you prefer using a Bot API token, you can build a similar watcher + aiogram sender. Note:
- The Bot API can only send files up to ~50 MB via sendDocument/sendVideo (as of writing).
- A bot must be an admin in the channel to post, or you can send via a bot using `send_message` with links.

## Troubleshooting
- If uploads fail with permission errors, ensure the account is admin in the channel and not banned.
- If a file uploads partially or errors out, check network stability and retry logs.

## License & legal
Use responsibly. I am not responsible for misuse.