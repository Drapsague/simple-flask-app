import sqlite3
import pickle
from security import hash_password

DBNAME = "site.db"


def get_db():
    conn = sqlite3.connect(DBNAME)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password TEXT NOT NULL,
        is_admin INTEGER DEFAULT 0
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        content TEXT,
        FOREIGN KEY(username) REFERENCES users(username)
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS profiles (
        username TEXT PRIMARY KEY,
        bio TEXT,
        website TEXT,
        theme_id INTEGER,
        FOREIGN KEY(username) REFERENCES users(username),
        FOREIGN KEY(theme_id) REFERENCES themes(id)
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS themes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        owner TEXT,
        color TEXT,
        font TEXT,
        data BLOB,
        FOREIGN KEY(owner) REFERENCES users(username)
    )
    """)
    conn.commit()
    conn.close()


initialize_db()


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
    cursor.execute(
        "INSERT INTO profiles (username, bio, website) VALUES (?, ?, ?)",
        (username, "", ""),
    )
    db.commit()
    db.close()


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


def add_post(username, content):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO posts (username, content) VALUES (?, ?)", (username, content)
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


def get_profile(username):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM profiles WHERE username = ?", (username,))
    row = cursor.fetchone()
    db.close()
    return row


def update_profile_field(username, field, value):
    db = get_db()
    cursor = db.cursor()
    assert field in ["bio", "website", "theme"], "Illegal profile field"
    cursor.execute(
        f"UPDATE profiles SET {field} = ? WHERE username = ?", (value, username)
    )
    db.commit()
    db.close()


def save_theme(owner, name, color, font, theme_obj):
    db = get_db()
    cursor = db.cursor()
    theme_blob = sqlite3.Binary(pickle.dumps(theme_obj))
    cursor.execute(
        "INSERT INTO themes (name, owner, color, font, data) VALUES (?, ?, ?, ?, ?)",
        (name, owner, color, font, theme_blob),
    )
    db.commit()
    db.close()


def import_theme(owner, fileobj, name):
    theme_obj = pickle.load(fileobj)
    color = theme_obj.get("color", "#ffffff")
    font = theme_obj.get("font", "Arial")
    save_theme(owner, name, color, font, theme_obj)


def list_themes_for_user_or_public(owner):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM themes WHERE owner=? OR owner IS NULL", (owner,))
    themes = cursor.fetchall()
    db.close()
    return themes


def get_theme_by_id(theme_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM themes WHERE id=?", (theme_id,))
    row = cursor.fetchone()
    db.close()
    return row


def set_user_theme(username, theme_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "UPDATE profiles SET theme_id=? WHERE username=?", (theme_id, username)
    )
    db.commit()
    db.close()


def get_user_theme_obj(username):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        """SELECT themes.* FROM profiles
           JOIN themes ON profiles.theme_id = themes.id
           WHERE profiles.username=?""",
        (username,),
    )
    row = cursor.fetchone()
    db.close()
    if not row or not row["data"]:
        return None
    return pickle.loads(row["data"])

