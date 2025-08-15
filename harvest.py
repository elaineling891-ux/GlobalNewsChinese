import requests
from bs4 import BeautifulSoup
import psycopg2
import os
import openai

DATABASE_URL = os.getenv("DATABASE_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

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
        created_at TIMESTAMP DEFAULT NOW()
    );
    """)
    conn.commit()
    cur.close()
    conn.close()

def save_news(title, url, content, source, image_url):
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute("SELECT id FROM news WHERE url=%s", (url,))
    if cur.fetchone():
        cur.close()
        conn.close()
        return
    cur.execute("""
        INSERT INTO news (title, url, content, source, image_url)
        VALUES (%s, %s, %s, %s, %s)
    """, (title, url, content, source, image_url))
    conn.commit()
    cur.close()
    conn.close()

def rewrite_content(original_content):
    try:
        prompt = f"将以下新闻改写成长篇文章，保持原意，不侵犯版权：\n{original_content}"
        resp = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role":"user","content":prompt}],
            temperature=0.7
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        print("改写失败:", e)
        return original_content

def fetch_news():
    init_db()
    url = "https://www.chinanews.com.cn/"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    try:
        resp = requests.get(url, headers=headers, timeout=30)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")
        articles = soup.select("div.news-item a")[:5]
        for a in articles:
            title = a.get_text(strip=True)
            href = a['href']
            content = title
            rewritten = rewrite_content(content)
            img_tag = a.find("img")
            image_url = img_tag['src'] if img_tag else ""
            save_news(title, href, rewritten, "Chinanews", image_url)
        print("抓取完成")
    except Exception as e:
        print("抓取出错:", e)
