#!/usr/bin/env python3
"""
Telethon-based folder watcher that uploads new files to a Telegram channel.

Usage:
  - Copy config.example.py -> config.py and fill values.
  - pip install -r requirements.txt
  - python bot.py
  - On first run Telethon asks for your phone number and code to login (creates SESSION_NAME.session)
Notes:
  - Make sure the account (user) you sign in with is admin or allowed to post to TARGET_CHANNEL.
  - This script moves uploaded files to UPLOADED_DIR or deletes them if configured.
"""
import asyncio
import logging
import os
import shutil
import sys
import time
from pathlib import Path

from telethon import TelegramClient, errors
from telethon.tl.types import InputPeerChannel
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

try:
    import config  # config.py must exist (copy from config.example.py)
except Exception as e:
    print("Missing or invalid config.py. Copy config.example.py -> config.py and edit.")
    raise

API_ID = 31101959
API_HASH = 3ca4f3e815c8e3df8aa1a00b8f81f22e
SESSION_NAME = getattr(config, "SESSION_NAME", "uploader_session")
TARGET_CHANNEL = config.TARGET_CHANNEL
WATCH_DIR = Path(config.WATCH_DIR)
UPLOADED_DIR = Path(config.UPLOADED_DIR)
ALLOWED_EXTENSIONS = set(getattr(config, "ALLOWED_EXTENSIONS", {".mkv", ".mp4", ".webm", ".avi"}))
CAPTION_TEMPLATE = getattr(config, "CAPTION_TEMPLATE", "{filename}")
DELETE_AFTER_UPLOAD = getattr(config, "DELETE_AFTER_UPLOAD", False)
LOG_LEVEL = getattr(config, "LOG_LEVEL", "INFO").upper()

# Setup logging
logging.basicConfig(
    format="%(asctime)s %(levelname)s %(message)s",
    level=getattr(logging, LOG_LEVEL, logging.INFO),
)
logger = logging.getLogger("uploader")

# Ensure folders exist
WATCH_DIR.mkdir(parents=True, exist_ok=True)
UPLOADED_DIR.mkdir(parents=True, exist_ok=True)

# Telethon client
client = TelegramClient(SESSION_NAME, API_ID, API_HASH)

# A simple in-memory set to avoid double-handling the same path in quick succession
_processing = set()


def human_size_mb(path: Path) -> float:
    try:
        return path.stat().st_size / (1024 * 1024)
    except Exception:
        return 0.0


async def send_file_with_progress(entity, path: Path):
    total = path.stat().st_size
    last_percent = -1

    def progress(current, t):
        nonlocal last_percent
        if t:
            percent = int(current * 100 / t)
            if percent != last_percent:
                logger.info("Uploading %s: %d%% (%d/%d bytes)", path.name, percent, current, t)
                last_percent = percent

    caption = CAPTION_TEMPLATE.format(filename=path.name, filesize_mb=human_size_mb(path))

    try:
        await client.send_file(entity, file=str(path), caption=caption, progress_callback=progress)
        logger.info("Upload complete: %s", path.name)
    except errors.rpcerrorlist.FileReferenceExpiredError as e:
        logger.warning("FileReferenceExpiredError for %s - retrying once", path.name)
        await client.send_file(entity, file=str(path), caption=caption, progress_callback=progress)
    except Exception:
        logger.exception("Failed to upload %s", path.name)
        raise


async def handle_new_file(path: str):
    path = Path(path)
    if not path.exists() or not path.is_file():
        return

    if path.suffix.lower() not in ALLOWED_EXTENSIONS:
        logger.info("Skipping file with unsupported extension: %s", path.name)
        return

    # Avoid double processing
    key = str(path.resolve())
    if key in _processing:
        return
    _processing.add(key)

    try:
        logger.info("Preparing to upload: %s", path.name)
        # Wait for the file to be fully written (size stable)
        stable = False
        last_size = -1
        for _ in range(30):  # up to ~30s
            try:
                size = path.stat().st_size
            except Exception:
                size = -1
            if size == last_size and size > 0:
                stable = True
                break
            last_size = size
            await asyncio.sleep(1)
        if not stable:
            logger.info("File %s may still be writing (proceeding anyway).", path.name)

        # Determine entity
        try:
            entity = await client.get_entity(TARGET_CHANNEL)
        except Exception as e:
            # Could be a username or numeric id; try as input
            logger.exception("Failed to resolve target channel entity: %s", TARGET_CHANNEL)
            raise

        # Upload
        await send_file_with_progress(entity, path)

        # Move/delete after upload
        if DELETE_AFTER_UPLOAD:
            try:
                path.unlink()
                logger.info("Deleted file after upload: %s", path.name)
            except Exception:
                logger.exception("Failed to delete %s", path.name)
        else:
            dest = UPLOADED_DIR / path.name
            # Avoid overwriting: add timestamp if exists
            if dest.exists():
                dest = UPLOADED_DIR / f"{int(time.time())}_{path.name}"
            try:
                shutil.move(str(path), str(dest))
                logger.info("Moved uploaded file to: %s", dest)
            except Exception:
                logger.exception("Failed to move uploaded file %s", path.name)

    finally:
        _processing.discard(key)


class NewFileHandler(FileSystemEventHandler):
    def __init__(self, loop):
        super().__init__()
        self.loop = loop

    def on_created(self, event):
        if event.is_directory:
            return
        logger.info("Detected new file: %s", event.src_path)
        # schedule async handler in existing loop
        asyncio.run_coroutine_threadsafe(handle_new_file(event.src_path), self.loop)

    def on_moved(self, event):
        # handle files moved into directory
        if event.is_directory:
            return
        logger.info("Detected moved file in: %s", event.dest_path)
        asyncio.run_coroutine_threadsafe(handle_new_file(event.dest_path), self.loop)


async def main():
    await client.start()  # will prompt for login on first run
    me = await client.get_me()
    logger.info("Logged in as %s (id=%s)", getattr(me, "username", me.phone), me.id)

    # Verify access to target channel
    try:
        entity = await client.get_entity(TARGET_CHANNEL)
        logger.info("Target channel resolved: %s", getattr(entity, "title", getattr(entity, "username", str(entity))))
    except Exception:
        logger.exception("Unable to resolve target channel. Make sure the account has permission to post there.")
        await client.disconnect()
        return

    # Start watchdog observer in a separate thread
    loop = asyncio.get_event_loop()
    event_handler = NewFileHandler(loop)
    observer = Observer()
    observer.schedule(event_handler, str(WATCH_DIR), recursive=False)
    observer.start()
    logger.info("Watching directory: %s", WATCH_DIR)

    try:
        # Keep running until Ctrl+C or disconnect
        await client.run_until_disconnected()
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    finally:
        observer.stop()
        observer.join()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Exit")
        sys.exit(0)
