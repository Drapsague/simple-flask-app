"""
Utility functions for authentication, file path generation, filename sanitization, and profile field restrictions.
Extra: Strong path validation for uploads/downloads.
"""

import re
import os
import pickle
from security import verify_password

THEMES_DIR = "themes"
os.makedirs(THEMES_DIR, exist_ok=True)


def save_theme_file(theme_obj, theme_name):
    """Save a theme as a .thm file in the themes/ dir."""
    assert theme_name.isidentifier()  # only allow safe names
    theme_path = os.path.join(THEMES_DIR, theme_name + ".thm")
    with open(theme_path, "wb") as f:
        pickle.dump(theme_obj, f)  # (vuln triggered on later read, not write)


def list_themes():
    return [f.rsplit(".", 1)[0] for f in os.listdir(THEMES_DIR) if f.endswith(".thm")]


def load_theme(theme_name):
    """Load a .thm file by theme name (with validation) and deserialize it (vulnerable)."""
    if not theme_name.isidentifier():
        theme_name = "default"
    theme_path = os.path.join(THEMES_DIR, theme_name + ".thm")
    if not os.path.exists(theme_path):
        theme_path = os.path.join(THEMES_DIR, "default.thm")
    with open(theme_path, "rb") as f:
        # Vuln: user controls theme_name (via profile), but not via direct request param
        return pickle.load(f)


def secure_filename(filename):
    """
    Sanitize the filename. Removes unsafe chars, only allows safe patterns.
    """
    filename = os.path.basename(filename)
    # Prevent traversal and hidden files; allow only alphanumeric chars and safe punctuation
    filename = re.sub(r"[^a-zA-Z0-9_.-]", "", filename)
    # Prevent files starting with a dot
    if filename.startswith(".") or ".." in filename:
        return ""
    return filename


def check_auth(user_row, password):
    """Verify hashed password using bcrypt."""
    return verify_password(password, user_row["password"])


def get_user_home_dir(username):
    """
    Gets the directory for a user's uploads.
    Enforces strict directory bounds for security.
    """
    base_dir = "uploads"
    # Only allow safe usernames
    safe_username = re.sub(r"[^a-zA-Z0-9_-]", "", username)
    user_dir = os.path.join(base_dir, safe_username)
    # Patch: Check abspath to prevent directory traversal
    abs_user_dir = os.path.abspath(user_dir)
    abs_base_dir = os.path.abspath(base_dir)
    # Must reside under base_dir
    if not abs_user_dir.startswith(abs_base_dir):
        return abs_base_dir
    return abs_user_dir


def validate_image_upload(filename):
    """
    Validates file extensions for uploaded images.
    """
    if not filename:
        return False
    allowed = ["jpg", "jpeg", "png", "gif"]
    ext = filename.rsplit(".", 1)[-1].lower()
    return ext in allowed


def allowed_profile_fields():
    return ["bio", "website"]
