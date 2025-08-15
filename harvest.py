import requests
from bs4 import BeautifulSoup
import psycopg2
from datetime import datetime
from openai import OpenAI
import os
import time
import random

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    cur.close()
    conn.close()

def save_news(title, url, content, source, image_url):
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO news (title, url, content, source, image_url, created_at)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (title, url, content, source, image_url, datetime.now()))
    conn.commit()
    cur.close()
    conn.close()

def get_latest_news(limit=10):
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute("""
        SELECT title, url, content, source, image_url, created_at
        FROM news ORDER BY created_at DESC LIMIT %s
    """, (limit,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    news_list = []
    for row in rows:
        news_list.append({
            "title": row[0],
            "url": row[1],
            "content": row[2],
            "source": row[3],
            "image_url": row[4],
            "created_at": row[5].isoformat()
        })
    return news_list

def rewrite_news(title, summary):
    prompt = f"""
    将以下新闻改写成原创文章，不要直接复制原文，并保持信息准确：
    标题：{title}
    内容：{summary}
    """
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

NEWS_SOURCES = [
    {"name": "联合新闻网", "url": "https://udn.com/news/index", "selector": "section.story-list a.story__headline"},
    {"name": "自由时报", "url": "https://news.ltn.com.tw/", "selector": "div.latestnews a"},
    {"name": "Yahoo 新闻华语", "url": "https://tw.news.yahoo.com/", "selector": "h3 a"}
]

def fetch_news():
    print("🟢 开始抓取新闻...")
    init_db()
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    
    for source in NEWS_SOURCES:
        try:
            resp = requests.get(source["url"], headers=headers, timeout=30)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            articles = soup.select(source["selector"])[:5]
            for a in articles:
                title = a.get_text(strip=True)
                href = a.get("href")
                if not href.startswith("http"):
                    href = source["url"].rstrip("/") + href
                try:
                    article_resp = requests.get(href, headers=headers, timeout=30)
                    article_resp.raise_for_status()
                    article_soup = BeautifulSoup(article_resp.text, "html.parser")
                    content_div = article_soup.find("article") or article_soup.find("div")
                    summary = content_div.get_text(strip=True) if content_div else title
                except:
                    summary = title
                rewritten = rewrite_news(title, summary)
                img_tag = article_soup.find("img")
                image_url = img_tag["src"] if img_tag else ""
                save_news(title, href, rewritten, source["name"], image_url)
                print(f"✅ 保存新闻: {title}")
                time.sleep(random.randint(3,10))
        except requests.exceptions.RequestException as e:
            print(f"❌ {source['name']} 抓取失败:", e)
    print("🟢 抓取完成")
