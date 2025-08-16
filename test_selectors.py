# test_selectors.py
import requests
from bs4 import BeautifulSoup

headers = {"User-Agent": "Mozilla/5.0"}

def test_udn():
    print("=== 联合新闻网 UDN ===")
    url = "https://udn.com/news/index"
    resp = requests.get(url, headers=headers)
    soup = BeautifulSoup(resp.text, "html.parser")
    articles = soup.select("section.story-list h3 a")[:5]
    if not articles:
        print("❌ 没抓到文章")
    for a in articles:
        print("✅", a.get_text(strip=True), a["href"])

def test_ltn():
    print("\n=== 自由时报 LTN ===")
    url = "https://news.ltn.com.tw/list/breakingnews"
    resp = requests.get(url, headers=headers)
    soup = BeautifulSoup(resp.text, "html.parser")
    articles = soup.select("ul.list li a.tit")[:5]
    if not articles:
        print("❌ 没抓到文章")
    for a in articles:
        print("✅", a.get_text(strip=True), a["href"])

def test_yahoo():
    print("\n=== Yahoo 新闻 ===")
    url = "https://tw.news.yahoo.com/"
    resp = requests.get(url, headers=headers)
    soup = BeautifulSoup(resp.text, "html.parser")
    articles = soup.select("h3 a")[:5]
    if not articles:
        print("❌ 没抓到文章")
    for a in articles:
        print("✅", a.get_text(strip=True), a["href"])

if __name__ == "__main__":
    test_udn()
    test_ltn()
    test_yahoo()
