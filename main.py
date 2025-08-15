from fastapi import FastAPI
from apscheduler.schedulers.background import BackgroundScheduler
from harvest import fetch_news
import psycopg2, os

app = FastAPI()
scheduler = BackgroundScheduler()

scheduler.add_job(fetch_news, 'interval', minutes=1)
scheduler.start()

@app.get("/", methods=["GET", "HEAD"])
async def read_root():
    return {"message": "自动华语新闻网站已启动"}

@app.get("/news")
async def list_news():
    DATABASE_URL = os.getenv("DATABASE_URL")
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute("SELECT id, title, url, content, source, image_url, created_at FROM news ORDER BY created_at DESC LIMIT 10")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    news_list = [{
        "id": r[0],
        "title": r[1],
        "url": r[2],
        "content": r[3],
        "source": r[4],
        "image_url": r[5],
        "created_at": r[6].isoformat()
    } for r in rows]
    return {"news": news_list}
