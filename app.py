from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    send_file,
)
import os

from db import (
    create_user,
    get_posts_for_user,
    get_user_by_username,
    get_profile,
    update_profile_field,
    set_user_theme,
    get_user_theme_obj,
    list_themes_for_user_or_public,
    import_theme,
    initialize_db,
    add_post,
    promote_to_admin,
    create_admin,
)
from utils import (
    secure_filename,
    check_auth,
    get_user_home_dir,
    validate_image_upload,
    allowed_profile_fields,
)
from security import secure_session

app = Flask(__name__)
app.secret_key = "super_secret_key"
app.config["UPLOAD_FOLDER"] = "uploads"
secure_session(app)
initialize_db()
create_admin()


def is_admin(username):
    user = get_user_by_username(username)
    return user and user["is_admin"]


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/register", methods=["POST"])
def register():
    username = request.form["username"]
    password = request.form["password"]
    if get_user_by_username(username):
        flash("Username already exists")
        return redirect(url_for("index"))
    create_user(username, password)
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


@app.route("/theme", methods=["GET", "POST"])
def theme():
    username = session.get("username")
    if not username:
        flash("Please login.")
        return redirect(url_for("index"))

    if request.method == "POST":
        file = request.files.get("file")
        theme_name = request.form.get("theme_name")
        if not file or not theme_name or not theme_name.isidentifier():
            flash("Bad theme.")
            return redirect(url_for("theme"))
        try:
            import_theme(username, file, theme_name)
            flash("Theme imported.")
        except Exception:
            flash("Failed to import theme.")
    themes = list_themes_for_user_or_public(username)
    return render_template("theme.html", themes=themes)


@app.route("/theme/choose", methods=["POST"])
def choose_theme():
    username = session.get("username")
    if not username:
        flash("Please login.")
        return redirect(url_for("index"))
    theme_id = request.form.get("theme_id")
    if theme_id:
        set_user_theme(username, theme_id)
        flash("Theme selected.")
    return redirect(url_for("profile", username=username))


@app.route("/profile/<username>", methods=["GET", "POST"])
def profile(username):
    if not session.get("username"):
        flash("Access denied")
        return redirect(url_for("index"))
    profile_data = get_profile(username)
    theme = get_user_theme_obj(username) or {"color": "#eee", "font": "Arial"}
    posts = get_posts_for_user(username)

    user_dir = get_user_home_dir(username)
    files = os.listdir(user_dir) if os.path.exists(user_dir) else []
    admin = is_admin(username)
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
    themes = list_themes_for_user_or_public(username)
    return render_template(
        "profile.html",
        username=username,
        profile=profile_data,
        posts=posts,
        files=files,
        theme=theme,
        themes=themes,
        admin=admin,
    )


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


@app.route("/add_post", methods=["POST"])
def add_post_route():
    username = session.get("username")
    if not username:
        flash("Please log in")
        return redirect(url_for("index"))
    content = request.form["content"]
    add_post(username, content)
    return redirect(url_for("profile", username=username))


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
    return redirect(url_for("profile", username=current_user))


if __name__ == "__main__":
    app.run(debug=False)
