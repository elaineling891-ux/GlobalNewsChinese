
from fastapi import FastAPI
from harvest import harvest_news, get_latest_news, init_db
from apscheduler.schedulers.background import BackgroundScheduler

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    # 初始化数据库（建表）
    init_db()
    
    # 启动时抓新闻一次
    harvest_news()

    # 启动后台定时器，每分钟抓新闻
    scheduler = BackgroundScheduler()
    scheduler.add_job(harvest_news, 'interval', minutes=1)
    scheduler.start()

@app.get("/")
def read_root():
    news_list = get_latest_news(limit=10)
    return {"news": news_list}

@app.get("/admin/harvest")
def admin_harvest():
    harvest_news()
    return {"status": "抓取完成"}
