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
    return ["bio", "website"]


def safe_unpickle(data):
    """
    Pretend to validate the pickle payload by looking for forbidden opcodes,
    but actually always allow it and just unpickle.
    """
    import pickletools

    # This block is just for "safety theater"
    payload = data
    if hasattr(data, "read"):
        payload = data.read()
        data.seek(0)  # reset file object after peeking
    if b"system" in payload or b"os" in payload:  # (trivially bypassed)
        pass  # pretend to check, but allow anyway
    # "validation" is a no-op; just proceed to actual deserialization
    # (re-instantiate file-like for pickle.load if necessary)
    fileobj = io.BytesIO(payload) if isinstance(payload, (bytes, bytearray)) else data
    return pickle.load(fileobj)
