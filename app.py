from datetime import datetime, date

from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import (LoginManager, UserMixin, login_user, logout_user,
                         login_required, current_user)
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config["SECRET_KEY"] = "change-this-to-a-random-secret"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///jobs.db"  # saved in instance/jobs.db

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"

STATUSES = ["Applied", "Interview", "Offer", "Rejected"]

ROLE_SUGGESTIONS = [
    "Python Developer", "Junior Python Developer", "Python Intern",
    "Backend Developer", "Full Stack Developer", "Flask Developer",
    "Django Developer", "Software Engineer", "Software Developer",
    "Web Developer", "Data Analyst", "Data Engineer", "Data Scientist",
    "Machine Learning Engineer", "Automation Engineer", "QA Engineer",
    "Test Engineer", "API Developer", "DevOps Engineer", "Trainee Engineer",
]

COMPANY_SUGGESTIONS = [
    "TCS", "Infosys", "Wipro", "HCLTech", "Cognizant", "Accenture",
    "Capgemini", "Tech Mahindra", "Zoho", "Freshworks", "Amazon", "Google",
    "Microsoft", "IBM", "Oracle", "Deloitte", "Mphasis", "LTIMindtree",
    "Hexaware", "Virtusa",
]


# ---------- Models ----------
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    jobs = db.relationship("Job", backref="user", lazy=True,
                           cascade="all, delete-orphan")


class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    company = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100))
    status = db.Column(db.String(20), default="Applied")
    applied_date = db.Column(db.Date, default=date.today)
    link = db.Column(db.String(300))
    notes = db.Column(db.Text)
    interviews = db.relationship("Interview", backref="job", lazy=True,
                                 cascade="all, delete-orphan")


class Interview(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey("job.id"), nullable=False)
    interview_date = db.Column(db.Date, nullable=False)
    mode = db.Column(db.String(30))
    notes = db.Column(db.Text)


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


# ---------- Helpers ----------
def parse_date(value):
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return date.today()


def fill_job(job):
    job.company = request.form["company"].strip()
    job.role = request.form["role"].strip()
    job.location = request.form.get("location", "").strip()
    job.status = request.form.get("status", "Applied")
    job.applied_date = parse_date(request.form.get("applied_date"))
    job.link = request.form.get("link", "").strip()
    job.notes = request.form.get("notes", "").strip()


def get_suggestions():
    """Your own past entries first, then the common suggestions."""
    my_companies = [c for (c,) in db.session.query(Job.company)
                    .filter(Job.user_id == current_user.id).distinct().all()]
    my_roles = [r for (r,) in db.session.query(Job.role)
                .filter(Job.user_id == current_user.id).distinct().all()]
    companies = my_companies + [c for c in COMPANY_SUGGESTIONS if c not in my_companies]
    roles = my_roles + [r for r in ROLE_SUGGESTIONS if r not in my_roles]
    return companies, roles


# ---------- Auth ----------
@app.route("/")
def home():
    return redirect(url_for("dashboard"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]
        if len(username) < 3 or len(password) < 6:
            flash("Username needs 3+ characters and password 6+ characters.", "error")
        elif User.query.filter_by(username=username).first():
            flash("Username already taken.", "error")
        else:
            user = User(username=username,
                        password_hash=generate_password_hash(password))
            db.session.add(user)
            db.session.commit()
            flash("Account created! Please log in.", "success")
            return redirect(url_for("login"))
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        user = User.query.filter_by(username=request.form["username"].strip()).first()
        if user and check_password_hash(user.password_hash, request.form["password"]):
            login_user(user)
            return redirect(url_for("dashboard"))
        flash("Invalid username or password.", "error")
    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out.", "success")
    return redirect(url_for("login"))


# ---------- Dashboard ----------
@app.route("/dashboard")
@login_required
def dashboard():
    q = request.args.get("q", "").strip()
    selected = request.args.get("status", "")

    query = Job.query.filter_by(user_id=current_user.id)
    if q:
        like = f"%{q}%"
        query = query.filter(db.or_(Job.company.ilike(like), Job.role.ilike(like)))
    if selected:
        query = query.filter(Job.status == selected)
    jobs = query.order_by(Job.applied_date.desc()).all()

    counts = {s: Job.query.filter_by(user_id=current_user.id, status=s).count()
              for s in STATUSES}
    return render_template("dashboard.html", jobs=jobs, counts=counts,
                           total=sum(counts.values()), statuses=STATUSES,
                           q=q, selected=selected)


# ---------- Jobs CRUD ----------
@app.route("/job/add", methods=["GET", "POST"])
@login_required
def add_job():
    if request.method == "POST":
        job = Job(user_id=current_user.id)
        fill_job(job)
        db.session.add(job)
        db.session.commit()
        flash("Job added!", "success")
        return redirect(url_for("dashboard"))
    companies, roles = get_suggestions()
    return render_template("job_form.html", job=None, statuses=STATUSES,
                           today=date.today().isoformat(),
                           companies=companies, roles=roles)


@app.route("/job/<int:job_id>/edit", methods=["GET", "POST"])
@login_required
def edit_job(job_id):
    job = Job.query.filter_by(id=job_id, user_id=current_user.id).first_or_404()
    if request.method == "POST":
        fill_job(job)
        db.session.commit()
        flash("Job updated!", "success")
        return redirect(url_for("dashboard"))
    companies, roles = get_suggestions()
    return render_template("job_form.html", job=job, statuses=STATUSES,
                           today=date.today().isoformat(),
                           companies=companies, roles=roles)


@app.route("/job/<int:job_id>/delete", methods=["POST"])
@login_required
def delete_job(job_id):
    job = Job.query.filter_by(id=job_id, user_id=current_user.id).first_or_404()
    db.session.delete(job)
    db.session.commit()
    flash("Job deleted.", "success")
    return redirect(url_for("dashboard"))


# ---------- Interviews ----------
@app.route("/interviews", methods=["GET", "POST"])
@login_required
def interviews():
    my_jobs = Job.query.filter_by(user_id=current_user.id).all()
    if request.method == "POST":
        job = Job.query.filter_by(id=request.form.get("job_id", type=int),
                                  user_id=current_user.id).first_or_404()
        db.session.add(Interview(
            job_id=job.id,
            interview_date=parse_date(request.form.get("interview_date")),
            mode=request.form.get("mode", ""),
            notes=request.form.get("notes", "").strip()))
        if job.status == "Applied":
            job.status = "Interview"
        db.session.commit()
        flash("Interview scheduled!", "success")
        return redirect(url_for("interviews"))

    items = (Interview.query.join(Job).filter(Job.user_id == current_user.id)
             .order_by(Interview.interview_date).all())
    return render_template("interviews.html", items=items, jobs=my_jobs,
                           today=date.today().isoformat())


@app.route("/interview/<int:iv_id>/delete", methods=["POST"])
@login_required
def delete_interview(iv_id):
    iv = (Interview.query.join(Job)
          .filter(Interview.id == iv_id, Job.user_id == current_user.id)
          .first_or_404())
    db.session.delete(iv)
    db.session.commit()
    flash("Interview removed.", "success")
    return redirect(url_for("interviews"))


with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)