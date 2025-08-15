import os
import psycopg2
from bs4 import BeautifulSoup
import requests
from datetime import datetime

DATABASE_URL = os.environ.get("DATABASE_URL")

def init_db():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS news (
            id SERIAL PRIMARY KEY,
            title TEXT,
            url TEXT,
            content TEXT,
            source TEXT,
            image_url TEXT,
            created_at TIMESTAMP
        )
    """)
    conn.commit()
    cur.close()
    conn.close()
    print("✅ 数据库初始化完成")

def save_news(title, url, content, source, image_url):
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO news (title, url, content, source, image_url, created_at)
            VALUES (%s,%s,%s,%s,%s,%s)
            ON CONFLICT DO NOTHING
        """, (title, url, content, source, image_url, datetime.now()))
        conn.commit()
        cur.close()
        conn.close()
        print(f"✅ 新闻保存成功: {title}")
    except Exception as e:
        print("❌ 保存新闻出错:", e)

def rewrite_content(content):
    # 这里简单返回原文，可替换为 OpenAI 改写逻辑
    return content

def fetch_news():
    print("🟢 开始抓取新闻...")
    init_db()
    url = "https://www.chinanews.com.cn/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }

    try:
        resp = requests.get(url, headers=headers, timeout=30)
        resp.raise_for_status()
        print("网页长度:", len(resp.text))
        soup = BeautifulSoup(resp.text, "lxml")

        # 针对中新网首页新闻区域的 selector
        articles = soup.select("div.content_left a")[:5]  # 抓取前5条新闻

        if not articles:
            print("⚠️ 没有抓到新闻，可能 selector 需要再次调整")
            return

        for a in articles:
            title = a.get_text(strip=True)
            href = a.get("href")
            if not href.startswith("http"):
                href = "https://www.chinanews.com.cn" + href
            content = title
            rewritten = rewrite_content(content)
            img_tag = a.find("img")
            image_url = img_tag["src"] if img_tag else ""
            save_news(title, href, rewritten, "Chinanews", image_url)

        print("🟢 抓取完成")
    except Exception as e:
        print("❌ 抓取出错:", e)
        
def get_latest_news(limit=10):
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute("""
            SELECT title, url, content, source, image_url, created_at
            FROM news ORDER BY created_at DESC LIMIT %s
        """, (limit,))
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return [{"title": r[0], "url": r[1], "content": r[2], "source": r[3], "image_url": r[4], "created_at": str(r[5])} for r in rows]
    except Exception as e:
        print("❌ 查询新闻出错:", e)
        return []
