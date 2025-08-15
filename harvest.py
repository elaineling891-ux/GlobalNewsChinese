def fetch_news():
    print("🟢 开始抓取新闻...")
    init_db()

    try:
        conn_test = psycopg2.connect(DATABASE_URL)
        print("✅ fetch_news: 数据库连接成功")
        conn_test.close()
    except Exception as e:
        print("❌ fetch_news: 数据库连接失败", e)
        return

    url = "https://www.chinanews.com.cn/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }

    try:
        resp = requests.get(url, headers=headers, timeout=30)
        resp.raise_for_status()
        print("网页长度:", len(resp.text))
        soup = BeautifulSoup(resp.text, "lxml")

        # 选中新网页新闻列表，保证可以抓到
        # 注意：这个 selector 需要根据网站实际结构调整
        articles = soup.select("div.content_list a")[:5]  # 抓前5条新闻

        if not articles:
            print("⚠️ 没有抓到新闻，可能 selector 需要调整")
        for a in articles:
            title = a.get_text(strip=True)
            href = a['href']
            if not href.startswith("http"):
                href = "https://www.chinanews.com.cn" + href
            content = title
            rewritten = rewrite_content(content)
            img_tag = a.find("img")
            image_url = img_tag['src'] if img_tag else ""
            save_news(title, href, rewritten, "Chinanews", image_url)

        print("🟢 抓取完成")
    except Exception as e:
        print("❌ 抓取出错:", e)
