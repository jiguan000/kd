import re
import logging
from dataclasses import dataclass
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup


logger = logging.getLogger(__name__)


@dataclass
class WechatArticle:
    title: str
    content_html: str


_WECHAT_BLOCK_KEYWORDS = [
    "环境异常",
    "访问过于频繁",
    "请在微信客户端打开",
    "为了保护你的网络安全",
    "Verify",
]


def _is_likely_blocked(html: str) -> bool:
    if not html:
        return True
    return any(kw in html for kw in _WECHAT_BLOCK_KEYWORDS)


def _clean_wechat_content_html(raw_html: str) -> str:
    """
    解决“能滚动但空白”的关键清理：
    1) 删除 script/style/noscript
    2) 去除 visibility:hidden / display:none / opacity:0 等隐藏样式
    3) img: data-src -> src
    """
    soup = BeautifulSoup(raw_html, "html.parser")

    for t in soup.find_all(["script", "style", "noscript"]):
        t.decompose()

    style_kill_patterns = [
        re.compile(r"visibility\s*:\s*hidden", re.I),
        re.compile(r"display\s*:\s*none", re.I),
        re.compile(r"opacity\s*:\s*0(\.0+)?", re.I),
        re.compile(r"height\s*:\s*0(px)?", re.I),
    ]

    for tag in soup.find_all(True):
        style = tag.get("style")
        if not style:
            continue

        parts = [p.strip() for p in style.split(";") if p.strip()]
        kept = []
        for p in parts:
            pl = p.lower()
            if any(pat.search(pl) for pat in style_kill_patterns):
                continue
            kept.append(p)

        if kept:
            tag["style"] = "; ".join(kept)
        else:
            del tag["style"]

    # 懒加载图片字段
    for img in soup.find_all("img"):
        if img.get("data-src"):
            img["src"] = img.get("data-src")
        if img.get("data-original") and not img.get("src"):
            img["src"] = img.get("data-original")
        if img.get("src", "").startswith("data:") and img.get("data-src"):
            img["src"] = img.get("data-src")

    return str(soup)


def rewrite_images_to_proxy(content_html: str, *, proxy_path: str = "/wechat/image") -> str:
    """
    把 <img src="https://mmbiz.qpic.cn/..."> 改写为
    <img src="/wechat/image?u=<urlencoded_original>">

    这样浏览器请求的是你自己后端，不会触发微信防盗链。
    """
    soup = BeautifulSoup(content_html, "html.parser")

    for img in soup.find_all("img"):
        img_url = img.get("src") or img.get("data-src")
        if not img_url or img_url.startswith("data:"):
            continue

        # 只代理微信 CDN（减少误代理站外图片）；要更激进可删除此判断
        if "mmbiz.qpic.cn" not in img_url and "mmbiz.qlogo.cn" not in img_url:
            continue

        img["src"] = f"{proxy_path}?u={quote(img_url, safe='')}"
        # 清理懒加载字段，避免前端覆盖
        if img.get("data-src"):
            del img["data-src"]
        if img.get("data-original"):
            del img["data-original"]

    return str(soup)


def fetch_wechat_article(url: str, *, image_proxy_path: str = "/wechat/image") -> WechatArticle:
    """
    输入：单篇公众号文章 URL（mp.weixin.qq.com/s/...）
    输出：标题 + 正文 HTML（图片已改写为代理接口，不落盘）
    """
    if not url or "mp.weixin.qq.com" not in url:
        raise ValueError("请输入合法的微信公众号文章链接（mp.weixin.qq.com）")

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/121.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Connection": "keep-alive",
        "Referer": "https://mp.weixin.qq.com/",
        "Upgrade-Insecure-Requests": "1",
    }

    sess = requests.Session()
    resp = sess.get(url, headers=headers, timeout=25)
    resp.raise_for_status()

    if not resp.encoding or resp.encoding.lower() == "iso-8859-1":
        resp.encoding = resp.apparent_encoding or "utf-8"

    html = resp.text or ""
    if _is_likely_blocked(html):
        raise ValueError("访问被微信风控拦截（环境异常/频率限制/需在微信客户端打开）")

    soup = BeautifulSoup(html, "html.parser")

    # 标题
    title = None
    og_title = soup.find("meta", property="og:title")
    if og_title and og_title.get("content"):
        title = og_title["content"].strip()
    if not title:
        h1 = soup.find("h1", class_="rich_media_title")
        if h1:
            title = h1.get_text(strip=True)
    if not title and soup.title and soup.title.string:
        title = soup.title.string.strip()

    title = re.sub(r"\s+", " ", title or "微信文章").strip()

    # 正文容器
    content_node = soup.find("div", id="js_content")
    if not content_node:
        content_node = soup.find("div", class_="rich_media_content")
    if not content_node:
        raise ValueError("未找到正文容器（js_content），可能链接异常或结构变化/受限")

    # 清理 + 图片改写为代理
    content_html = _clean_wechat_content_html(str(content_node))
    content_html = rewrite_images_to_proxy(content_html, proxy_path=image_proxy_path)

    text_len = len(BeautifulSoup(content_html, "html.parser").get_text(strip=True))
    if text_len < 30:
        raise ValueError("正文内容为空或过短，疑似仍被限制访问")

    return WechatArticle(title=title, content_html=content_html)


def fetch_wechat_image_bytes(img_url: str) -> tuple[bytes, str]:
    """
    后端代理：从微信 CDN 拉取图片，返回 (bytes, content_type)
    """
    if not img_url:
        raise ValueError("img_url empty")

    # 简单限制：只允许微信图片域名，避免被当成开放代理滥用
    if "mmbiz.qpic.cn" not in img_url and "mmbiz.qlogo.cn" not in img_url:
        raise ValueError("only wechat image domains are allowed")

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/121.0.0.0 Safari/537.36"
        ),
        # 关键：带上微信接受的 Referer
        "Referer": "https://mp.weixin.qq.com/",
        "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Connection": "keep-alive",
    }

    r = requests.get(img_url, headers=headers, timeout=25)
    r.raise_for_status()

    content_type = r.headers.get("Content-Type") or "image/jpeg"
    return r.content, content_type
