# AI Assistance Disclosure:
# ChatGPT was used to help review, debug, and refine parts of this project.
# I am responsible for understanding, testing, and maintaining the code.
import os
import secrets
import sqlite3
from datetime import date
from functools import wraps
from pathlib import Path
from urllib.parse import urlparse

from flask import (
    Flask,
    abort,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
import click
from dotenv import load_dotenv
from werkzeug.security import check_password_hash, generate_password_hash

load_dotenv()

app = Flask(__name__)


@app.template_filter("deadline_info")
def deadline_info(deadline):
    try:
        deadline_date = date.fromisoformat(str(deadline)[:10])
    except (ValueError, TypeError):
        return {"text": "Deadline unavailable", "class": "deadline-normal"}

    days_left = (deadline_date - date.today()).days
    if days_left < 0:
        return {"text": "Deadline passed", "class": "deadline-expired"}
    if days_left == 0:
        return {"text": "Deadline is today", "class": "deadline-urgent"}
    if days_left <= 7:
        text = "1 day left" if days_left == 1 else f"{days_left} days left"
        return {"text": text, "class": "deadline-urgent"}
    if days_left <= 30:
        return {"text": f"{days_left} days left", "class": "deadline-soon"}
    return {"text": f"{days_left} days left", "class": "deadline-normal"}


app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY")
if not app.config["SECRET_KEY"]:
    raise RuntimeError(
        "SECRET_KEY is missing. Set it before starting CampusPath."
    )
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = (
    os.environ.get("SESSION_COOKIE_SECURE", "").lower() == "true"
)
DATABASE = Path(__file__).with_name("campuspath.db")
SCHEMA = Path(__file__).with_name("schema.sql")


def admin_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        user_id = session.get("user_id")
        if user_id is None:
            return redirect(url_for("login"))

        connection = get_db_connection()
        try:
            user = connection.execute(
                "SELECT is_admin FROM users WHERE id = ?",
                (user_id,),
            ).fetchone()
        finally:
            connection.close()

        if user is None:
            session.clear()
            return redirect(url_for("login"))
        if not user["is_admin"]:
            abort(403)
        return view(*args, **kwargs)

    return wrapped_view


@app.context_processor
def inject_csrf_token():
    return {"csrf_token": lambda: session.setdefault("csrf_token", secrets.token_hex(32))}


@app.before_request
def protect_post_requests():
    if request.method == "POST":
        submitted_token = request.form.get("csrf_token", "")
        session_token = session.get("csrf_token", "")
        if not session_token or not secrets.compare_digest(
            submitted_token, session_token
        ):
            abort(400, description="Invalid or missing CSRF token.")


def get_db_connection():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_db():
    connection = get_db_connection()
    try:
        connection.executescript(SCHEMA.read_text(encoding="utf-8"))
        user_columns = {
            row["name"] for row in connection.execute("PRAGMA table_info(users)")
        }
        if "is_admin" not in user_columns:
            connection.execute(
                """
                ALTER TABLE users
                ADD COLUMN is_admin INTEGER NOT NULL DEFAULT 0
                CHECK (is_admin IN (0, 1))
                """
            )

        opportunity_columns = {
            row["name"]
            for row in connection.execute("PRAGMA table_info(opportunities)")
        }
        if "is_published" not in opportunity_columns:
            connection.execute(
                """
                ALTER TABLE opportunities
                ADD COLUMN is_published INTEGER NOT NULL DEFAULT 1
                CHECK (is_published IN (0, 1))
                """
            )

        opportunity_count = connection.execute(
            "SELECT COUNT(*) FROM opportunities"
        ).fetchone()[0]
        if opportunity_count == 0:
            connection.executemany(
                """
                INSERT INTO opportunities
                (title, organization, category, description, deadline, application_url)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        "Undergraduate Tech Scholarship",
                        "Example Foundation",
                        "Scholarship",
                        "Financial support for eligible undergraduate students in technology-related fields.",
                        "2027-03-31",
                        "https://example.com/scholarship",
                    ),
                    (
                        "Student Web Development Internship",
                        "Example Tech Company",
                        "Internship",
                        "A learning opportunity for students interested in web development.",
                        "2027-04-15",
                        "https://example.com/internship",
                    ),
                    (
                        "National Student Innovation Challenge",
                        "Example Innovation Hub",
                        "Competition",
                        "An opportunity for students to present innovative solutions to real problems.",
                        "2027-05-20",
                        "https://example.com/competition",
                    ),
                ],
            )
        connection.commit()
    finally:
        connection.close()


init_db()


def ensure_configured_admin():
    username = os.environ.get("ADMIN_USERNAME", "").strip()
    password = os.environ.get("ADMIN_PASSWORD", "")
    if not username and not password:
        return
    if not username or not password:
        raise RuntimeError(
            "Set both ADMIN_USERNAME and ADMIN_PASSWORD."
        )
    if len(username) > 50 or len(password) < 12:
        raise RuntimeError(
            "Admin username must be at most 50 characters, "
            "and admin password must be at least 12 characters."
        )

    connection = get_db_connection()
    try:
        password_hash = generate_password_hash(password)
        existing = connection.execute(
            "SELECT id FROM users WHERE username = ?",
            (username,),
        ).fetchone()
        if existing:
            connection.execute(
                """
                UPDATE users
                SET is_admin = 1, password_hash = ?
                WHERE username = ?
                """,
                (password_hash, username),
            )
        else:
            connection.execute(
                """
                INSERT INTO users (username, password_hash, is_admin)
                VALUES (?, ?, 1)
                """,
                (username, password_hash),
            )
        connection.commit()
    finally:
        connection.close()


ensure_configured_admin()


@app.cli.command("promote-admin")
@click.argument("username")
def promote_admin(username):
    """Promote an existing account using a trusted local CLI."""
    connection = get_db_connection()
    try:
        result = connection.execute(
            "UPDATE users SET is_admin = 1 WHERE username = ?",
            (username,),
        )
        if result.rowcount == 0:
            raise click.ClickException(f"No account found for username '{username}'.")
        connection.commit()
    finally:
        connection.close()
    click.echo(f"Administrator access granted to {username}.")


@app.route("/")
def index():
    connection = get_db_connection()
    try:
        opportunities = connection.execute(
            """
            SELECT *
            FROM opportunities
            WHERE is_published = 1
            ORDER BY deadline ASC
            """
        ).fetchall()
        saved_ids = set()
        if "user_id" in session:
            saved_rows = connection.execute(
                """
                SELECT opportunity_id
                FROM saved_opportunities
                WHERE user_id = ?
                """,
                (session["user_id"],),
            ).fetchall()
            saved_ids = {row["opportunity_id"] for row in saved_rows}
    finally:
        connection.close()
    today = date.today().isoformat()
    return render_template(
        "index.html",
        opportunities=opportunities,
        saved_ids=saved_ids,
        today=today,
        is_admin=bool(session.get("is_admin")),
    )


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirmation = request.form.get("confirmation", "")

        if not username or not password or not confirmation:
            flash("All fields are required.")
            return render_template("register.html")

        if len(username) > 50:
            flash("Username must be 50 characters or fewer.")
            return render_template("register.html")

        if len(password) < 8:
            flash("Password must contain at least 8 characters.")
            return render_template("register.html")

        if password != confirmation:
            flash("Passwords do not match.")
            return render_template("register.html")

        connection = get_db_connection()
        try:
            connection.execute(
                "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                (username, generate_password_hash(password)),
            )
            connection.commit()
        except sqlite3.IntegrityError:
            connection.rollback()
            flash("That username may already be taken.")
            return render_template("register.html")
        finally:
            connection.close()

        flash("Account created. You can now log in.")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        connection = get_db_connection()
        try:
            user = connection.execute(
                "SELECT * FROM users WHERE username = ?",
                (username,),
            ).fetchone()
        finally:
            connection.close()

        if user is None or not check_password_hash(user["password_hash"], password):
            flash("Invalid username or password.")
            return render_template("login.html")

        session.clear()
        session["user_id"] = user["id"]
        session["username"] = user["username"]
        session["is_admin"] = bool(user["is_admin"])
        return redirect(url_for("index"))

    return render_template("login.html")


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/save/<int:opportunity_id>", methods=["POST"])
def save_opportunity(opportunity_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = get_db_connection()
    try:
        opportunity = connection.execute(
            "SELECT id FROM opportunities WHERE id = ? AND is_published = 1",
            (opportunity_id,),
        ).fetchone()
        if opportunity is None:
            abort(404)

        connection.execute(
            """
            INSERT INTO saved_opportunities (user_id, opportunity_id)
            VALUES (?, ?)
            ON CONFLICT(user_id, opportunity_id) DO NOTHING
            """,
            (session["user_id"], opportunity_id),
        )
        connection.commit()
    finally:
        connection.close()

    flash("Opportunity saved successfully.")
    return redirect(url_for("index"))


@app.route("/unsave/<int:opportunity_id>", methods=["POST"])
def unsave_opportunity(opportunity_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = get_db_connection()
    try:
        result = connection.execute(
            """
            DELETE FROM saved_opportunities
            WHERE user_id = ? AND opportunity_id = ?
            """,
            (session["user_id"], opportunity_id),
        )
        connection.commit()
    finally:
        connection.close()

    if result.rowcount > 0:
        flash("Opportunity removed from your saved list.")
    else:
        flash("That opportunity was not in your saved list.")

    return redirect(url_for("index"))


@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = get_db_connection()
    try:
        saved_opportunities = connection.execute(
            """
            SELECT
                opportunities.*,
                saved_opportunities.status,
                saved_opportunities.saved_at,
                saved_opportunities.id AS saved_id
            FROM saved_opportunities
            JOIN opportunities
                ON opportunities.id = saved_opportunities.opportunity_id
            WHERE saved_opportunities.user_id = ?
            ORDER BY opportunities.deadline ASC
            """,
            (session["user_id"],),
        ).fetchall()
    finally:
        connection.close()

    return render_template(
        "dashboard.html",
        opportunities=saved_opportunities,
    )


@app.route("/update-status/<int:saved_id>", methods=["POST"])
def update_status(saved_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    allowed_statuses = {
        "Interested",
        "Preparing",
        "Applied",
        "Accepted",
        "Rejected",
    }
    status = request.form.get("status", "")
    if status not in allowed_statuses:
        abort(400)

    connection = get_db_connection()
    try:
        result = connection.execute(
            """
            UPDATE saved_opportunities
            SET status = ?
            WHERE id = ? AND user_id = ?
            """,
            (status, saved_id, session["user_id"]),
        )
        if result.rowcount == 0:
            abort(404)
        connection.commit()
    finally:
        connection.close()

    return redirect(url_for("dashboard"))


def validate_opportunity_form():
    fields = {
        key: request.form.get(key, "").strip()
        for key in (
            "title",
            "organization",
            "category",
            "description",
            "deadline",
            "application_url",
        )
    }
    if any(not value for value in fields.values()):
        return fields, "All opportunity fields are required."
    if len(fields["title"]) > 200 or len(fields["organization"]) > 120:
        return fields, "Title must be 200 characters or fewer and organization 120 or fewer."
    if len(fields["category"]) > 50 or len(fields["description"]) > 5000:
        return fields, "Category must be 50 characters or fewer and description 5,000 or fewer."

    try:
        deadline = date.fromisoformat(fields["deadline"])
    except ValueError:
        return fields, "Enter a valid deadline in YYYY-MM-DD format."
    if deadline.isoformat() != fields["deadline"]:
        return fields, "Enter a valid deadline in YYYY-MM-DD format."

    try:
        parsed_url = urlparse(fields["application_url"])
        hostname = parsed_url.hostname
        port = parsed_url.port
    except ValueError:
        return fields, "Application URL must be a valid http:// or https:// URL."
    if (
        len(fields["application_url"]) > 2048
        or parsed_url.scheme not in {"http", "https"}
        or not parsed_url.netloc
        or not hostname
        or port == 0
        or parsed_url.username
        or parsed_url.password
    ):
        return fields, "Application URL must be a valid http:// or https:// URL."
    return fields, None


@app.route("/admin")
@admin_required
def admin_dashboard():
    connection = get_db_connection()
    try:
        opportunities = connection.execute(
            """
            SELECT opportunities.*,
                   (SELECT COUNT(*) FROM saved_opportunities
                    WHERE opportunity_id = opportunities.id) AS saved_count
            FROM opportunities
            ORDER BY opportunities.id DESC
            """
        ).fetchall()
    finally:
        connection.close()
    return render_template("admin.html", opportunities=opportunities)


@app.route("/admin/opportunities/new", methods=["GET", "POST"])
@admin_required
def create_opportunity():
    fields = {}
    if request.method == "POST":
        fields, error = validate_opportunity_form()
        if error:
            flash(error)
            return render_template(
                "admin_opportunity_form.html",
                opportunity=fields,
                heading="Add opportunity",
            ), 400

        connection = get_db_connection()
        try:
            connection.execute(
                """
                INSERT INTO opportunities
                (title, organization, category, description, deadline, application_url,
                 is_published)
                VALUES (?, ?, ?, ?, ?, ?, 0)
                """,
                tuple(fields[key] for key in (
                    "title", "organization", "category", "description",
                    "deadline", "application_url",
                )),
            )
            connection.commit()
        finally:
            connection.close()
        flash("Opportunity created as a draft.")
        return redirect(url_for("admin_dashboard"))

    return render_template(
        "admin_opportunity_form.html",
        opportunity=fields,
        heading="Add opportunity",
    )


@app.route("/admin/opportunities/<int:opportunity_id>/edit", methods=["GET", "POST"])
@admin_required
def edit_opportunity(opportunity_id):
    connection = get_db_connection()
    try:
        opportunity = connection.execute(
            "SELECT * FROM opportunities WHERE id = ?",
            (opportunity_id,),
        ).fetchone()
        if opportunity is None:
            abort(404)
        opportunity = dict(opportunity)

        if request.method == "POST":
            fields, error = validate_opportunity_form()
            if error:
                flash(error)
                return render_template(
                    "admin_opportunity_form.html",
                    opportunity=fields,
                    heading="Edit opportunity",
                ), 400
            connection.execute(
                """
                UPDATE opportunities
                SET title = ?, organization = ?, category = ?, description = ?,
                    deadline = ?, application_url = ?
                WHERE id = ?
                """,
                (
                    fields["title"],
                    fields["organization"],
                    fields["category"],
                    fields["description"],
                    fields["deadline"],
                    fields["application_url"],
                    opportunity_id,
                ),
            )
            connection.commit()
    finally:
        connection.close()

    if request.method == "POST":
        flash("Opportunity updated.")
        return redirect(url_for("admin_dashboard"))
    return render_template(
        "admin_opportunity_form.html",
        opportunity=opportunity,
        heading="Edit opportunity",
    )


@app.route("/admin/opportunities/<int:opportunity_id>/publish", methods=["POST"])
@admin_required
def toggle_opportunity_published(opportunity_id):
    connection = get_db_connection()
    try:
        result = connection.execute(
            """
            UPDATE opportunities
            SET is_published = CASE is_published WHEN 1 THEN 0 ELSE 1 END
            WHERE id = ?
            """,
            (opportunity_id,),
        )
        if result.rowcount == 0:
            abort(404)
        connection.commit()
    finally:
        connection.close()
    flash("Opportunity publication status updated.")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/opportunities/<int:opportunity_id>/delete", methods=["POST"])
@admin_required
def delete_opportunity(opportunity_id):
    connection = get_db_connection()
    try:
        opportunity = connection.execute(
            "SELECT id FROM opportunities WHERE id = ?",
            (opportunity_id,),
        ).fetchone()
        if opportunity is None:
            abort(404)

        result = connection.execute(
            """
            DELETE FROM opportunities
            WHERE id = ? AND is_published = 0 AND NOT EXISTS (
                SELECT 1 FROM saved_opportunities
                WHERE opportunity_id = ?
            )
            """,
            (opportunity_id, opportunity_id),
        )
        if result.rowcount == 0:
            current = connection.execute(
                "SELECT is_published FROM opportunities WHERE id = ?",
                (opportunity_id,),
            ).fetchone()
            if current is None:
                abort(404)
            if current["is_published"]:
                flash("Unpublish this opportunity before deleting it.")
                return redirect(url_for("admin_dashboard"))
            flash(
                "This opportunity cannot be deleted because students have saved it. "
                "Saved opportunities must remain in the system."
            )
            return redirect(url_for("admin_dashboard"))
        connection.commit()
    finally:
        connection.close()
    flash("Opportunity deleted.")
    return redirect(url_for("admin_dashboard"))


if __name__ == "__main__":
    app.run(debug=True)
