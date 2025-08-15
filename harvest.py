import requests
from bs4 import BeautifulSoup
import psycopg2
from datetime import datetime
from openai import OpenAI
import os

# 初始化 OpenAI
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# 数据库 URL，从环境变量读取
DATABASE_URL = os.environ.get("DATABASE_URL")

def init_db():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    # 创建表格（如果不存在）
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


def fetch_news():
    print("🟢 开始抓取新闻...")
    init_db()
    url = "https://www.sinchew.com.my/"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

    try:
        resp = requests.get(url, headers=headers, timeout=30)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # 星洲网新闻列表
        articles = soup.select("div.list-group-item a")[:5]  # 前5条新闻

        if not articles:
            print("⚠️ 没有抓到新闻，可能 selector 需要调整")
            return

        for a in articles:
            title = a.get_text(strip=True)
            href = a.get("href")
            if not href.startswith("http"):
                href = "https://www.sinchew.com.my" + href

            # 抓取新闻正文
            try:
                article_resp = requests.get(href, headers=headers, timeout=30)
                article_resp.raise_for_status()
                article_soup = BeautifulSoup(article_resp.text, "html.parser")
                content_div = article_soup.select_one("div.article-content")
                summary = content_div.get_text(strip=True) if content_div else title
            except Exception:
                summary = title  # 如果抓正文失败，用标题代替

            # 改写为原创文章
            rewritten = rewrite_news(title, summary)

            # 图片
            img_tag = article_soup.find("img")
            image_url = img_tag["src"] if img_tag else ""

            save_news(title, href, rewritten, "SinChew", image_url)
            print(f"✅ 保存新闻: {title}")

        print("🟢 抓取完成")

    except Exception as e:
        print("❌ 抓取出错:", e)
