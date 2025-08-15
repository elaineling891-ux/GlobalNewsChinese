from fastapi import FastAPI
from apscheduler.schedulers.background import BackgroundScheduler
from harvest import fetch_news
import psycopg2, os

app = FastAPI()
scheduler = BackgroundScheduler()

# 每分钟抓一次新闻
scheduler.add_job(fetch_news, 'interval', minutes=1)
scheduler.start()

# 根路径，不用 methods 参数，兼容旧版本 FastAPI
@app.get("/")
async def read_root():
    return {"message": "自动华语新闻网站已启动"}

# 新闻列表接口
@app.get("/news")
async def list_news():
    DATABASE_URL = os.getenv("DATABASE_URL")
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute("""
        SELECT id, title, url, content, source, image_url, created_at 
        FROM news 
        ORDER BY created_at DESC LIMIT 10
    """)
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
