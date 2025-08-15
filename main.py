from fastapi import FastAPI
from harvest import fetch_news, init_db
import threading

app = FastAPI()

# 启动时初始化数据库
@app.on_event("startup")
def startup_event():
    init_db()
    # 启动后台线程定时抓新闻
    def run_fetch():
        import time
        while True:
            fetch_news()
            time.sleep(60)  # 每分钟抓一次
    threading.Thread(target=run_fetch, daemon=True).start()

@app.get("/")
def read_root():
    return {"message": "自动华语新闻网站已启动"}

@app.get("/news")
def get_news():
    from harvest import get_latest_news
    news_list = get_latest_news(limit=10)
    return {"news": news_list}
