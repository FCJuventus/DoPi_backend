import os
import sqlite3
from typing import List
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from jinja2 import Environment, FileSystemLoader

# --------- Простая БД SQLite ---------
DB_PATH = "data/dopi.db"
os.makedirs("data", exist_ok=True)
with sqlite3.connect(DB_PATH) as conn:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            price_pi REAL DEFAULT 0
        )
    """)
    conn.commit()

# --------- FastAPI + Jinja ---------
app = FastAPI()
env = Environment(loader=FileSystemLoader("templates"))
app.mount("/static", StaticFiles(directory="static"), name="static")

class JobIn(BaseModel):
    title: str
    description: str = ""
    price_pi: float = 0.0

class JobOut(JobIn):
    id: int

def db_query(query: str, args=(), fetchone=False):
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute(query, args)
        conn.commit()
        return cur.fetchone() if fetchone else cur.fetchall()

# --------- Страницы ---------
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    template = env.get_template("index.html")
    rows = db_query("SELECT id, title, description, price_pi FROM jobs ORDER BY id DESC")
    jobs = [{"id": r[0], "title": r[1], "description": r[2], "price_pi": r[3]}] if rows else []
    return template.render(jobs=jobs)

@app.get("/healthz")
def healthz():
    return {"status": "ok"}

# --------- API ---------
@app.post("/api/jobs", response_model=JobOut)
def create_job(job: JobIn):
    db_query(
        "INSERT INTO jobs (title, description, price_pi) VALUES (?, ?, ?)",
        (job.title, job.description, job.price_pi)
    )
    row = db_query("SELECT id, title, description, price_pi FROM jobs ORDER BY id DESC LIMIT 1", fetchone=True)
    return {"id": row[0], "title": row[1], "description": row[2], "price_pi": row[3]}

@app.get("/api/jobs", response_model=List[JobOut])
def list_jobs():
    rows = db_query("SELECT id, title, description, price_pi FROM jobs ORDER BY id DESC")
    return [{"id": r[0], "title": r[1], "description": r[2], "price_pi": r[3]} for r in rows]
