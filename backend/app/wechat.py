import re
from dataclasses import dataclass

import requests
from bs4 import BeautifulSoup


@dataclass
class WechatArticle:
    title: str
    content_html: str


def fetch_wechat_article(url: str) -> WechatArticle:
    response = requests.get(url, timeout=15)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    title = soup.title.string.strip() if soup.title and soup.title.string else "微信文章"
    article = soup.find("div", id="js_content") or soup.body
    content_html = str(article) if article else response.text

    title = re.sub(r"\s+", " ", title).strip()
    return WechatArticle(title=title, content_html=content_html)
