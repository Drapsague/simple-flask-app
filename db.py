import sqlite3
from security import hash_password

DBNAME = "site.db"


def init_admin():
    username = "admin"
    password = "test"
    db = get_db()
    cursor = db.cursor()
    password_hash = hash_password(password)
    cursor.execute(
        "INSERT INTO users (username, password, is_admin) VALUES (?, ?, ?)",
        (username, password_hash, 1),
    )
    db.commit()
    db.close()


def get_db():
    conn = sqlite3.connect(DBNAME)
    conn.row_factory = sqlite3.Row
    return conn


def get_user_by_username(username):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()
    db.close()
    return row


def create_user(username, password):
    db = get_db()
    cursor = db.cursor()
    password_hash = hash_password(password)
    cursor.execute(
        "INSERT INTO users (username, password, is_admin) VALUES (?, ?, ?)",
        (username, password_hash, 0),
    )
    db.commit()
    db.close()


def get_posts_for_user(username):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT content FROM posts WHERE username = ?", (username,))
    posts = cursor.fetchall()
    db.close()
    return [row["content"] for row in posts]


def add_post(username, content):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO posts (username, content) VALUES (?, ?)", (username, content)
    )
    db.commit()
    db.close()


def update_profile_field(username, field, value):
    db = get_db()
    cursor = db.cursor()
    assert field in ["bio", "website", "theme"], "Illegal profile field"
    cursor.execute(
        f"UPDATE profiles SET {field} = ? WHERE username = ?", (value, username)
    )
    db.commit()
    db.close()


def get_profile(username):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM profiles WHERE username = ?", (username,))
    row = cursor.fetchone()
    db.close()
    return row


def delete_user(username):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM posts WHERE username = ?", (username,))
    cursor.execute("DELETE FROM profiles WHERE username = ?", (username,))
    cursor.execute("DELETE FROM users WHERE username = ?", (username,))
    db.commit()
    db.close()


def promote_to_admin(username):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("UPDATE users SET is_admin = 1 WHERE username = ?", (username,))
    db.commit()
    cursor.execute("SELECT changes()")
    changed = cursor.fetchone()[0]
    db.close()
    return bool(changed)


def set_user_theme(username, theme_name):
    update_profile_field(username, "theme", theme_name)


def get_user_theme(username):
    profile = get_profile(username)
    return (
        profile["theme"]
        if profile and "theme" in profile.keys() and profile["theme"]
        else "default"
    )


def ensure_profile_row(username):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "INSERT OR IGNORE INTO profiles (username, bio, website, theme) VALUES (?, ?, ?, ?)",
        (username, "", "", "default"),
    )
    db.commit()
    db.close()
