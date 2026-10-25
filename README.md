# Smart Job Tracker

A Flask web app to track job applications and interviews.

## Features
- User registration and login (password hashing with Werkzeug, sessions with Flask-Login)
- Add, edit, delete job applications (CRUD)
- Search by company or role, and filter by status
- Dashboard with status counts and a doughnut chart (Chart.js)
- Interview scheduling linked to each job
- SQLite database using Flask-SQLAlchemy

## Screenshots
![Dashboard](screenshots/dashboard.png)
![Add Job](screenshots/add-job.png)
![Interviews](screenshots/interviews.png)

## Tech Stack
Python, Flask, Flask-SQLAlchemy, Flask-Login, SQLite, HTML, CSS, Jinja2

## Setup
```bash
git clone <your-repo-url>
cd smart-job-tracker
pip install -r requirements.txt
python app.py
```
Open http://127.0.0.1:5000 in your browser.

## Project Structure
```
app.py            # routes and database models
templates/        # HTML templates
static/style.css  # styling
instance/jobs.db  # SQLite database (auto-created)
```