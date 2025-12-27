# Copy to config.py and fill in values
# TELEGRAM (user) credentials — required for uploading files >50MB or for using a user account to post:
API_ID = 31101959              # integer from https://my.telegram.org
API_HASH = "3ca4f3e815c8e3df8aa1a00b8f81f22e"
SESSION_NAME = "uploader_session.abid"  # file created to store session (e.g., uploader_session.session)

# TARGET: channel username (e.g. "@yourdatabasechannel") or numeric id (e.g. -1001234567890)
TARGET_CHANNEL = "@fryy7rrl"

# Folder to watch for new episode files
WATCH_DIR = "./watch"

# After successful upload files are moved to this folder
UPLOADED_DIR = "./uploaded"

# Allowed extensions to upload
ALLOWED_EXTENSIONS = {".mkv", ".mp4", ".webm", ".avi", ".srt", ".ass", ".zip"}

# Caption template for uploads. You can use {filename} and {filesize_mb}.
CAPTION_TEMPLATE = "New episode uploaded: {filename}\nSize: {filesize_mb:.1f} MB"

# If you want the script to delete the file after upload (True/False)
DELETE_AFTER_UPLOAD = False

# Logging level: "INFO" or "DEBUG"
LOG_LEVEL = "INFO"
