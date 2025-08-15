from fastapi import FastAPI
from harvest import fetch_news, init_db, get_latest_news

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    init_db()

@app.get("/")
def read_root():
    return {"message": "自动华语新闻网站已启动"}

@app.get("/news")
def read_news(limit: int = 10):
    news_list = get_latest_news(limit=limit)
    return {"news": news_list}

@app.post("/fetch")
def fetch_news_endpoint():
    fetch_news()
    return {"status": "抓取完成"}
