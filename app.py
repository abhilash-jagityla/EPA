import os
import re
from datetime import datetime
from io import BytesIO

from flask import (
    Flask, request, render_template, send_file,
    jsonify, redirect, url_for, flash
)
from flask_login import (
    LoginManager, login_user, logout_user,
    login_required, current_user
)
from flask_migrate import Migrate
from werkzeug.utils import secure_filename

import pandas as pd
import pdfplumber

from config import Config
from models import db, User
from forms import LoginForm, RegistrationForm
from pdf_extractor import PDFFieldExtractor

# ──────────────────────────────────────────────────────────────
# App & Extension setup
# ──────────────────────────────────────────────────────────────
app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
migrate = Migrate(app, db)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# ─── Patch: disable login redirects & CSRF when running tests ───
if app.config.get("TESTING"):          # set in tests via app.config['TESTING']=True
    app.config["LOGIN_DISABLED"] = True
    app.config["WTF_CSRF_ENABLED"] = False
    login_manager.login_view = None
# ──────────────────────────────────────────────────────────────

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Ensure upload folder exists
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# ──────────────────────────────────────────────────────────────
# Helper functions
# ──────────────────────────────────────────────────────────────
ALLOWED_EXTENSIONS = {"pdf"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def extract_variables(pdf_path, patterns):
    results = {key: [] for key in patterns.keys()}
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            for var, pattern in patterns.items():
                matches = re.finditer(pattern, text)
                results[var].extend(m.group() for m in matches)
    return results


DEFAULT_PATTERNS = {
    "emails": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
    "phone_numbers": r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",
    "dates": r"\b\d{2}[-/]\d{2}[-/]\d{4}\b",
    "dollar_amounts": r"\$\s*\d+(?:,\d{3})*(?:\.\d{2})?",
    "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
}

# ──────────────────────────────────────────────────────────────
# Auth routes
# ──────────────────────────────────────────────────────────────
@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            return redirect(url_for("dashboard"))
        flash("Invalid username or password")
    return render_template("login.html", form=form)


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    form = RegistrationForm()
    if form.validate_on_submit():
        if User.query.filter_by(username=form.username.data).first():
            flash("Username already taken")
            return redirect(url_for("register"))
        if User.query.filter_by(email=form.email.data).first():
            flash("Email already registered")
            return redirect(url_for("register"))

        new_user = User(username=form.username.data, email=form.email.data)
        new_user.set_password(form.password.data)
        db.session.add(new_user)
        db.session.commit()

        flash("Registration successful")
        return redirect(url_for("login"))

    return render_template("register.html", form=form)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))

# ──────────────────────────────────────────────────────────────
# Main application routes
# ──────────────────────────────────────────────────────────────
@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html")


@app.route("/", methods=["GET"])
@login_required
def index():
    return redirect(url_for("dashboard"))


@app.route("/upload", methods=["POST"])
@login_required
def upload_file():
    if "files[]" not in request.files:
        flash("No files selected")
        return redirect(url_for("dashboard"))

    files = request.files.getlist("files[]")
    if not files or all(f.filename == "" for f in files):
        flash("No selected files")
        return redirect(url_for("dashboard"))

    all_results = []

    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_filename = f"{timestamp}_{filename}"
            pdf_path = os.path.join(app.config["UPLOAD_FOLDER"], unique_filename)
            file.save(pdf_path)

            try:
                with PDFFieldExtractor(pdf_path) as extractor:
                    fields = extractor.extract_fields()
                    fields["Source_File"] = filename
                    all_results.append(fields)
            except Exception as e:
                flash(f"Error processing {filename}: {e}")
            finally:
                os.remove(pdf_path)
        else:
            flash(f"Invalid file type for {file.filename}. Only PDF allowed")

    if not all_results:
        flash("No data extracted from uploaded files.")
        return redirect(url_for("dashboard"))

    # Build Excel
    df = pd.DataFrame(all_results)
    cols = ["Source_File"] + [c for c in df.columns if c != "Source_File"]
    df = df[cols]

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    excel_filename = f"extracted_data_{timestamp}.xlsx"
    excel_path = os.path.join(app.config["UPLOAD_FOLDER"], excel_filename)

    with pd.ExcelWriter(excel_path, engine="xlsxwriter") as writer:
        df.to_excel(writer, sheet_name="Extracted Data", index=False)
        workbook = writer.book
        ws = writer.sheets["Extracted Data"]
        header_fmt = workbook.add_format(
            {"bold": True, "text_wrap": True, "valign": "top", "bg_color": "#D9EAD3", "border": 1}
        )
        for col_num, col_name in enumerate(df.columns):
            ws.write(0, col_num, col_name, header_fmt)
            ws.set_column(col_num, col_num, 15)

    return send_file(
        excel_path,
        as_attachment=True,
        download_name=excel_filename,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@app.route("/download/<filename>")
@login_required
def download_file(filename):
    try:
        return send_file(os.path.join(app.config["UPLOAD_FOLDER"], filename), as_attachment=True)
    except Exception as e:
        flash(f"Error downloading file: {e}")
        return redirect(url_for("dashboard"))


@app.route("/patterns", methods=["GET"])
@login_required
def get_patterns():
    return jsonify(DEFAULT_PATTERNS)

# ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=8000, debug=True)
