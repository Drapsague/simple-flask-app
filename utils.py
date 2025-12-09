import os
import io
import re
import pickle


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
    return ["bio", "website", "notification_url"]


class SUnpickler(pickle.Unpickler):
    def find_class(self, module, name):
        return getattr(__import__(module), name)


def safe_unpickle(data):
    fileobj = data if hasattr(data, "read") else io.BytesIO(data)
    return SUnpickler(fileobj).load()
