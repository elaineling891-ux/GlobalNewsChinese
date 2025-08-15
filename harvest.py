
import re, os
import psycopg2
import requests
from bs4 import BeautifulSoup

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
        created_at TIMESTAMP DEFAULT NOW()
    );
    """)
    conn.commit()
    cur.close()
    conn.close()

def is_chinese(text, threshold=0.3):
    if not text:
        return False
    cn_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
    return cn_chars / max(len(text),1) >= threshold

def extract_fulltext(url):
    try:
        r = requests.get(url, timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')
        paragraphs = soup.find_all('p')
        return '\n'.join(p.get_text() for p in paragraphs if p.get_text())
    except:
        return None

def save_news(title, url, content, source, image_url=None):
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO news (title, url, content, source, image_url)
        VALUES (%s, %s, %s, %s, %s)
    """, (title, url, content, source, image_url))
    conn.commit()
    cur.close()
    conn.close()

def get_latest_news(limit=10):
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute("""SELECT title, url, content, source, image_url, created_at
                   FROM news ORDER BY created_at DESC LIMIT %s""", (limit,))
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

def harvest_news():
    rss_sources = [
        {"name": "联合早报", "url": "https://www.zaobao.com/feeds/all.rss"},
        {"name": "凤凰网", "url": "https://news.ifeng.com/rss/index.xml"},
        {"name": "中新网", "url": "http://www.chinanews.com/rss/scroll-news.xml"}
    ]
    for source in rss_sources:
        try:
            r = requests.get(source['url'], timeout=10)
            soup = BeautifulSoup(r.text, 'xml')
            items = soup.find_all('item')[:5]  # 每个源抓前5篇
            for item in items:
                title = item.title.text if item.title else "无标题"
                url = item.link.text if item.link else None
                fulltext = extract_fulltext(url)
                if fulltext and is_chinese(fulltext):
                    save_news(title, url, fulltext, source['name'])
        except Exception as e:
            print("抓取出错:", source['name'], e)
