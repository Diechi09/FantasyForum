# Fantasy Forum
THE ULTIMATE PLACE TO DISCUSS ALL STUFF FANTASY, WHETHER THAT MEANS A SIMPLE TRADE QUESTION OR JUST SHOWING OFF YOUR KNOWLEDGE.
SEE HOW THE PEOPLE FEEL ABOUT PLAYERS, HEAR THE LATEST UPDATES AND WIN YOUR LEAGUE.

Here is a complete guide to running and exploring the Flask app locally.

## What you get
- User registration/login with password hashing and persistent sessions.
- Create, edit, delete, and comment on posts with flairs for **TRADE HELP**, **WAIVER WIRE ADVICE**, **INJURY TALK**, or **OTHER**.
- Search and pagination for posts via the JSON API.
- Health checks and Prometheus-friendly metrics (with a lightweight fallback when `prometheus_client` is not installed).
- Optional Azure Application Insights tracing when the `opencensus-ext-azure` dependency is available.

## NEED
- Python 3.10+
- (Optional) Docker + Docker Compose for containerized runs

## 1) Clone / open the project
```bash
cd /pathtotheproject
```

## 2) Create & activate a virtual environment
**Windows (PowerShell)**
```
py -3 -m venv .venv
. .\.venv\Scripts\Activate.ps1
```
**macOS / Linux**
```
python3 -m venv .venv
source .venv/bin/activate
```

## 3) Install dependencies
requirements.txt has all the stuff you will need, so download that
```
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 4) Run the app
```
python app.py
```
- The server should be live and you can open at: http://127.0.0.1:5000
- The SQLite database is created automatically (including the `flair` column) when the server starts.

## 5) Useful pages
- Home (`/`): See all posts that are being made by other people (filter by flair from the UI).
- About (`/about`): Quick summary of the project.
- API Demo (`/api-demo`): Search posts and download JSON exports without leaving the browser.
- Login/Register (`/login`, `/register`): Create an account to publish or comment.
- Posts: Create `/post/new`, edit `/post/<id>/edit`, delete `/post/<id>/delete`, and view `/post/<id>`.
- Health + monitoring: `/health` and `/api/health` return `{"status": "ok"}`; `/metrics` exposes Prometheus metrics.

## 6) JSON API quick reference
- `GET /api/posts?flair=<flair>&q=<text>&page=<page>&per_page=<1-50>`: Paginated posts with optional text search and flair filter.
- `GET /api/posts/<id>`: Single post payload including content.
- `GET /api/posts/<id>/comments`: Comments for a post.
- `GET /api/stats`: Counts per flair plus the five latest posts.
- `GET /api/export/posts`: Download all posts as a JSON file.

## 7) Docker (optional)
```bash
docker build -t fantasy-forum .
docker run -p 5000:5000 fantasy-forum
```
Or use Compose:
```bash
docker-compose up --build
```

## 8) To Run Tests
```
pytest --cov=app --cov-branch --cov-report=term-missing --cov-fail-under=90
```
