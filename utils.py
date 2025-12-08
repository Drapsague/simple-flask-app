import os
import re
import yaml


def secure_filename(filename):
    filename = os.path.basename(filename)
    filename = re.sub(r"[^a-zA-Z0-9_.-]", "", filename)
    if filename.startswith(".") or ".." in filename:
        return ""
    return filename


def check_auth(user_row, password):
    from security import verify_password

    return verify_password(password, user_row["password"])


def get_user_home_dir(username):
    base_dir = "uploads"
    safe_username = re.sub(r"[^a-zA-Z0-9_-]", "", username)
    user_dir = os.path.join(base_dir, safe_username)
    abs_user_dir = os.path.abspath(user_dir)
    abs_base_dir = os.path.abspath(base_dir)
    if not abs_user_dir.startswith(abs_base_dir):
        return abs_base_dir
    return abs_user_dir


def validate_image_upload(filename):
    if not filename:
        return False
    allowed = ["jpg", "jpeg", "png", "gif"]
    ext = filename.rsplit(".", 1)[-1].lower()
    return ext in allowed


def allowed_profile_fields():
    return ["bio", "website"]


def load_yaml_safe(data):
    """A 'broken' loader: loads untrusted YAML with yaml.Loader (unsafe)."""
    import io

    if hasattr(data, "read"):
        data = data.read()
    return yaml.load(data, Loader=yaml.Loader)

