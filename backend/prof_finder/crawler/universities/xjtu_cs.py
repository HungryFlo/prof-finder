"""Crawler for XJTU School of Computer Science and Technology.

Covers all five teacher categories:
  - 教授     http://www.cs.xjtu.edu.cn/szdw/jsml/js.htm
  - 研究员   http://www.cs.xjtu.edu.cn/szdw/jsml/yjy1.htm
  - 副教授   http://www.cs.xjtu.edu.cn/szdw/jsml/fjs1.htm
  - 高工     http://www.cs.xjtu.edu.cn/szdw/jsml/gg1.htm
  - 讲师及其他 http://www.cs.xjtu.edu.cn/szdw/jsml/jsjqt.htm

Page protection: The site uses a JS challenge (solves a hardcoded math problem,
posts to /dynamic_challenge, then sets a client_id cookie). This module handles
the challenge automatically using the requests session.

HTML structure (as of 2025):
    <div class="per clearfix">
        <div class="person-photo"><a href="<profile_url>">...</a></div>
        <div class="person-produce clearfix">
            <div class="person-produce-top">
                <a class="more" href="<profile_url>">了解详细</a>
                <h3>姓名  (职称)</h3>
            </div>
            <div class="person-produce-content">
                <div class="person-produce-content-left">
                    <ul>
                        <li>办公室：...</li>
                        <li>电话：...</li>
                        <li>邮箱：email@xjtu.edu.cn</li>
                        <li>博士生导师</li>  <!-- optional -->
                    </ul>
                </div>
                <div class="person-produce-content-right">
                    <h4>研究方向：</h4>
                    <p>方向一、方向二、方向三。</p>
                </div>
            </div>
        </div>
    </div>
"""

import re
import time
import logging
from typing import Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from .base import UniversityCrawlerBase

logger = logging.getLogger(__name__)

_BASE_URL = "http://www.cs.xjtu.edu.cn"
_AFFILIATION = "西安交通大学计算机科学与技术学院"

# All teacher category pages, in display order
_CATEGORY_PAGES: list[tuple[str, str]] = [
    ("教授",     f"{_BASE_URL}/szdw/jsml/js.htm"),
    ("研究员",   f"{_BASE_URL}/szdw/jsml/yjy1.htm"),
    ("副教授",   f"{_BASE_URL}/szdw/jsml/fjs1.htm"),
    ("高工",     f"{_BASE_URL}/szdw/jsml/gg1.htm"),
    ("讲师及其他", f"{_BASE_URL}/szdw/jsml/jsjqt.htm"),
]

# Delimiters used inside research direction text
_INTEREST_SPLIT_RE = re.compile(r"[、，,；;。\n]+")


class XJTUCSCrawler(UniversityCrawlerBase):
    """Crawl the full professor list from XJTU CS department website."""

    university_id = "xjtu-cs"
    display_name = "西安交通大学 - 计算机科学与技术学院"
    crawl_base_url = _BASE_URL

    def crawl_all(self, delay: float = 2.0) -> list[dict]:
        """Crawl all teachers from all XJTU CS department category pages.

        Categories covered: 教授、研究员、副教授、高工、讲师及其他.

        The site is protected by a JS challenge. This method solves the
        challenge once using the first category page, then reuses the session
        cookie for all subsequent requests.

        Args:
            delay: Seconds to wait between category page requests.

        Returns:
            List of teacher dicts (see :class:`.base.UniversityCrawlerBase`).

        Raises:
            RuntimeError: If the first category page is unreachable.
        """
        session = self._make_session()

        results: list[dict] = []
        challenge_solved = False

        for category_name, url in _CATEGORY_PAGES:
            # Solve challenge on the first page only; cookie reused after that
            if not challenge_solved:
                self._solve_challenge(session, url)
                challenge_solved = True

            logger.debug("爬取分类 %s: %s", category_name, url)
            response = session.get(url, timeout=15)
            if response.status_code != 200:
                logger.warning(
                    "跳过分类 %s，HTTP %s", category_name, response.status_code
                )
                continue

            response.encoding = "utf-8"
            page_results = self._parse_list_page(response.text)
            logger.debug("分类 %s 解析到 %d 人", category_name, len(page_results))
            results.extend(page_results)

            if delay > 0:
                time.sleep(delay)

        return results

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _make_session() -> requests.Session:
        session = requests.Session()
        session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                "Referer": _BASE_URL,
            }
        )
        return session

    @staticmethod
    def _solve_challenge(session: requests.Session, url: str) -> None:
        """Detect and solve the JS bot challenge, acquiring a client_id cookie.

        The page embeds two JS variables:
            var challengeId = "<id>";
            var answer = <number>;

        These are posted to ``/dynamic_challenge`` in exchange for the cookie.
        If the page is already accessible (no challenge script present),
        this function returns immediately.
        """
        try:
            response = session.get(url, timeout=15)
        except requests.RequestException as exc:
            raise RuntimeError(f"无法连接到目标网站: {exc}") from exc

        body = response.text
        cid_match = re.search(r'challengeId\s*=\s*"([^"]+)"', body)
        ans_match = re.search(r'\bvar\s+answer\s*=\s*(\d+)', body)

        if not cid_match:
            return  # No challenge present

        if not ans_match:
            raise RuntimeError("发现 JS 挑战但无法提取 answer 值")

        payload = {
            "challenge_id": cid_match.group(1),
            "answer": int(ans_match.group(1)),
            "browser_info": {
                "userAgent": "Mozilla/5.0",
                "language": "zh-CN",
                "platform": "Win32",
                "cookieEnabled": True,
                "hardwareConcurrency": 8,
                "deviceMemory": 8,
                "timezone": "Asia/Shanghai",
            },
        }
        try:
            resp = session.post(
                f"{_BASE_URL}/dynamic_challenge", json=payload, timeout=10
            )
            data = resp.json()
            if not data.get("success"):
                raise RuntimeError(f"JS 挑战失败: {data}")
        except (requests.RequestException, ValueError) as exc:
            raise RuntimeError(f"JS 挑战请求失败: {exc}") from exc

    @staticmethod
    def _parse_list_page(html: str) -> list[dict]:
        """Parse all professor cards from the list page HTML.

        Args:
            html: Full HTML text of the list page.

        Returns:
            Parsed professor list.
        """
        soup = BeautifulSoup(html, "html.parser")
        cards = soup.find_all("div", class_="per")
        results: list[dict] = []

        for card in cards:
            try:
                prof = XJTUCSCrawler._parse_card(card)
                if prof:
                    results.append(prof)
            except Exception as exc:
                logger.warning("解析教授卡片失败，跳过: %s", exc)

        return results

    @staticmethod
    def _parse_card(card: BeautifulSoup) -> Optional[dict]:
        """Extract structured data from a single professor card element."""
        # --- Name and title ---
        h3 = card.find("h3")
        if not h3:
            return None
        raw_name = h3.get_text(strip=True)
        # Format: "董小社  (教授)" — strip the title part
        name = re.sub(r"\s*[\(（].*?[\)）]\s*$", "", raw_name).strip()
        if not name:
            return None

        # --- Profile URL (用作 source_url) ---
        detail_link = card.select_one("a.more")
        source_url: Optional[str] = None
        if detail_link and detail_link.get("href"):
            source_url = urljoin(_BASE_URL + "/", str(detail_link["href"]).strip())

        # --- Contact details (left column) ---
        email: Optional[str] = None
        li_items = card.select(".person-produce-content-left li")
        for li in li_items:
            text = li.get_text(strip=True)
            if text.startswith("邮箱："):
                email = text.removeprefix("邮箱：").strip() or None

        # --- Research interests (right column) ---
        research_interests: list[str] = []
        right_col = card.select_one(".person-produce-content-right p")
        if right_col:
            raw_interests = right_col.get_text(strip=True)
            parts = [p.strip() for p in _INTEREST_SPLIT_RE.split(raw_interests) if p.strip()]
            research_interests = parts

        return {
            "name": name,
            "affiliation": _AFFILIATION,
            "email": email,
            "homepage": source_url,
            "research_interests": research_interests,
            "source_url": source_url or _BASE_URL,
        }
