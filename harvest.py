import requests
from bs4 import BeautifulSoup
import psycopg2
from datetime import datetime
from openai import OpenAI
import os
import time
import random

# 初始化 OpenAI
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
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Referer": "https://www.sinchew.com.my/"
    }

    try:
        resp = requests.get(url, headers=headers, timeout=30)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # 星洲网新闻列表（根据首页结构选择合适的 selector）
        articles = soup.select("div.list-group-item a")[:5]  # 前5条新闻
        if not articles:
            print("⚠️ 没有抓到新闻，可能 selector 需要调整")
            return

        for a in articles:
            title = a.get_text(strip=True)
            href = a.get("href")
            if not href.startswith("http"):
                href = "https://www.sinchew.com.my" + href

            # 抓取正文
            try:
                article_resp = requests.get(href, headers=headers, timeout=30)
                article_resp.raise_for_status()
                article_soup = BeautifulSoup(article_resp.text, "html.parser")
                content_div = article_soup.select_one("div.article-content")
                summary = content_div.get_text(strip=True) if content_div else title
            except Exception:
                summary = title

            # 改写为原创文章
            rewritten = rewrite_news(title, summary)

            # 图片
            img_tag = article_soup.find("img")
            image_url = img_tag["src"] if img_tag else ""

            save_news(title, href, rewritten, "SinChew", image_url)
            print(f"✅ 保存新闻: {title}")

            # 随机延时 5~10 秒，防止被封
            time.sleep(random.randint(5, 10))

        print("🟢 抓取完成")

    except requests.exceptions.HTTPError as e:
        print("❌ HTTP 错误:", e)
    except requests.exceptions.RequestException as e:
        print("❌ 网络请求错误:", e)
    except Exception as e:
        print("❌ 其他错误:", e)
