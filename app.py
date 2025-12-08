from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    send_file,
    make_response,
)
import os
import sqlite3

from db import (
    get_user_by_username,
    create_user,
    get_posts_for_user,
    add_post,
    update_profile_field,
    get_profile,
    delete_user,
    promote_to_admin,
    set_user_theme,
    get_user_theme,
    ensure_profile_row,
)

from utils import (
    secure_filename,
    check_auth,
    get_user_home_dir,
    validate_image_upload,
    allowed_profile_fields,
    save_theme_file,
    list_themes,
    load_theme,
)

import os
import sqlite3
from security import secure_session
from cache import UserCacheManager

app = Flask(__name__)
app.secret_key = "super_secret_key"
app.config["UPLOAD_FOLDER"] = "uploads"
secure_session(app)
# init_admin()

DBNAME = "site.db"


def initialize_db():
    conn = sqlite3.connect(DBNAME)
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
        FOREIGN KEY(username) REFERENCES users(username)
    )
    """)
    conn.commit()
    conn.close()


initialize_db()


def is_admin(username):
    user = get_user_by_username(username)
    return user and user["is_admin"]


@app.route("/")
def index():
    return render_template("index.html")


def get_profile_cache_mgr(username, extra_key="profile_preview"):
    mgr = UserCacheManager(username)
    # This key is sometimes attacker-influenced via request or hidden param
    mgr.set_cache_key(extra_key)
    return mgr


@app.route("/register", methods=["POST"])
def register():
    username = request.form["username"]
    password = request.form["password"]
    if get_user_by_username(username):
        flash("Username already exists")
        return redirect(url_for("index"))
    create_user(username, password)
    conn = sqlite3.connect(DBNAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO profiles (username, bio, website) VALUES (?, ?, ?)",
        (username, "", ""),
    )
    conn.commit()
    conn.close()
    session["username"] = username
    return redirect(url_for("profile", username=username))


@app.route("/login", methods=["POST"])
def login():
    username = request.form["username"]
    password = request.form["password"]
    user = get_user_by_username(username)
    if user and check_auth(user, password):
        session["username"] = username
        return redirect(url_for("profile", username=username))
    else:
        flash("Invalid credentials")
        return redirect(url_for("index"))


@app.route("/profile/<username>", methods=["GET", "POST"])
def profile(username):
    if not session.get("username") or session["username"] != username:
        flash("Access denied")
        return redirect(url_for("index"))
    ensure_profile_row(username)
    posts = get_posts_for_user(username)
    user_dir = get_user_home_dir(username)
    files = os.listdir(user_dir) if os.path.exists(user_dir) else []
    profile_data = get_profile(username)

    # Load the theme object for rendering (THIS IS THE DESERIALIZATION SINK)
    theme_name = profile_data.get("theme", "default") if profile_data else "default"
    theme = load_theme(theme_name)

    # e.g., theme = {"color": "teal", "font": "Verdana", "cssclass": "dark-mode"}
    if request.method == "POST":
        field = request.form["field"]
        value = request.form["value"]
        if field in allowed_profile_fields():
            update_profile_field(username, field, value)
            flash("Profile updated")
        elif field == "theme":
            set_user_theme(username, value)
            flash("Theme changed")
        else:
            flash("Invalid field")
        return redirect(url_for("profile", username=username))
    themes = list_themes()
    return render_template(
        "profile.html",
        username=username,
        posts=posts,
        files=files,
        profile=profile_data,
        themes=themes,
        theme=theme,
    )


@app.route("/theme", methods=["GET", "POST"])
def theme():
    """Handle theme upload/import/export."""
    username = session.get("username")
    if not username:
        flash("Please login.")
        return redirect(url_for("index"))

    if request.method == "POST":  # import/upload
        file = request.files.get("file")
        if not file or not file.filename.endswith(".thm"):
            flash("Upload a valid .thm file.")
            return redirect(url_for("theme"))
        theme_name = request.form.get("theme_name")
        try:
            theme_obj = pickle.load(file)  # Import pickle; no code runs yet!
            save_theme_file(theme_obj, theme_name)
            flash("Theme imported.")
        except Exception:
            flash("Failed to import theme.")
    themes = list_themes()
    return render_template(
        "theme.html", themes=themes, current_theme=get_user_theme(username)
    )


@app.route("/theme/export/<theme_name>")
def theme_export(theme_name):
    """Export .thm file."""
    if not theme_name.isidentifier():
        flash("Bad theme name.")
        return redirect(url_for("theme"))
    theme_path = os.path.join("themes", theme_name + ".thm")
    if not os.path.exists(theme_path):
        flash("Theme not found.")
        return redirect(url_for("theme"))
    return send_file(theme_path, as_attachment=True, download_name=theme_name + ".thm")


@app.route("/add_post", methods=["POST"])
def add_post_route():
    username = session.get("username")
    if not username:
        flash("Please log in")
        return redirect(url_for("index"))
    content = request.form["content"]
    add_post(username, content)
    return redirect(url_for("profile", username=username))


@app.route("/upload", methods=["POST"])
def upload():
    username = session.get("username")
    if not username:
        flash("Please log in")
        return redirect(url_for("index"))
    file = request.files["file"]
    if not file:
        flash("No file uploaded")
        return redirect(url_for("profile", username=username))
    filename = secure_filename(file.filename)
    if not filename or not validate_image_upload(filename):
        flash("Invalid image type")
        return redirect(url_for("profile", username=username))
    user_dir = get_user_home_dir(username)
    os.makedirs(user_dir, exist_ok=True)
    file_path = os.path.join(user_dir, filename)
    file_path = os.path.abspath(file_path)
    if not file_path.startswith(os.path.abspath(user_dir)):
        flash("Bad file path")
        return redirect(url_for("profile", username=username))
    file.save(file_path)
    flash("Upload successful")
    return redirect(url_for("profile", username=username))


@app.route("/download/<username>/<filename>")
def download(username, filename):
    if not session.get("username"):
        flash("Please log in")
        return redirect(url_for("index"))
    safe_filename = secure_filename(filename)
    if not safe_filename:
        flash("Invalid filename")
        return redirect(url_for("profile", username=session["username"]))
    user_dir = get_user_home_dir(username)
    file_path = os.path.join(user_dir, safe_filename)
    file_path = os.path.abspath(file_path)
    if not file_path.startswith(os.path.abspath(user_dir)):
        flash("Invalid file path")
        return redirect(url_for("profile", username=session["username"]))
    if not os.path.exists(file_path):
        flash("File does not exist")
        return redirect(url_for("profile", username=session["username"]))
    return send_file(file_path, as_attachment=True)


@app.route("/admin/delete/<username>", methods=["POST"])
def admin_delete(username):
    current_user = session.get("username")
    if is_admin(current_user):
        delete_user(username)
        flash("User deleted.")
    else:
        flash("Admin access required.")
    return redirect(url_for("index"))


@app.route("/remove_account", methods=["POST"])
def remove_account():
    username = request.form.get("username")
    delete_user(username)
    flash("Account deleted.")
    return redirect(url_for("index"))


# ---- NEW FEATURE: Admin Promotion ----
@app.route("/admin/promote", methods=["POST"])
def admin_promote():
    current_user = session.get("username")
    if not is_admin(current_user):
        flash("Admin access required.")
        return redirect(url_for("index"))
    promote_username = request.form.get("username")
    if promote_to_admin(promote_username):
        flash(f"User {promote_username} promoted to admin.")
    else:
        flash("Promotion failed. User may not exist.")
    return redirect(url_for("index"))


# ---- Add promotion form to the index page (example) ----
@app.context_processor
def inject_admin():
    return dict(is_admin=lambda: is_admin(session.get("username", "")))


# In templates/index.html, you can add:

if __name__ == "__main__":
    app.run(debug=False)
