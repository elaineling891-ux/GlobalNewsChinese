from fastapi import FastAPI
from apscheduler.schedulers.background import BackgroundScheduler
from harvest import fetch_news, init_db
import os

app = FastAPI()

@app.on_event("startup")
def startup_event():
    init_db()
    scheduler = BackgroundScheduler()
    # 每分钟抓一次，可改为 minutes=5
    scheduler.add_job(fetch_news, 'interval', minutes=1)
    scheduler.start()
    print("🟢 APScheduler 已启动，自动抓新闻任务已注册")

@app.get("/")
def read_root():
    return {"message": "自动华语新闻网站已启动"}

@app.get("/news")
def get_news():
    from harvest import get_latest_news
    news_list = get_latest_news(limit=10)
    return {"news": news_list}
