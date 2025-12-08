from passlib.hash import bcrypt


def hash_password(password):
    """Return a bcrypt hash of the password, truncating to 72 bytes."""
    if isinstance(password, str):
        password = password.encode("utf-8")
    if len(password) > 72:
        password = password[:72]
    return bcrypt.hash(password)


def verify_password(password, password_hash):
    """Verify a plaintext password against its bcrypt hash, truncating to 72 bytes."""
    if isinstance(password, str):
        password = password.encode("utf-8")
    if len(password) > 72:
        password = password[:72]
    return bcrypt.verify(password, password_hash)


def secure_session(app):
    """
    Set secure session cookie flags for Flask.
    Place this right after the Flask app is initialized.
    """
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SECURE"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

