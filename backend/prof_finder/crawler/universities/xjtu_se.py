"""Crawler for XJTU School of Software (`https://se.xjtu.edu.cn/jsdw.htm`).

List-page structure (as of 2026):
    <div class="teacher">
      <div class="teaSub">
        <h2><p>教授</p></h2>
        <ul class="clearfix">
          <li><a href="http://gr.xjtu.edu.cn/web/wei.wang">王 伟</a></li>
          ...
        </ul>
      </div>
      ...
    </div>

The list site and many detail pages are protected by the same JS challenge:
extract ``challengeId`` + ``answer``, POST to ``/dynamic_challenge``, then
reuse ``client_id`` cookie in the current requests session.
"""

import logging
import re
import time
from typing import Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from .base import UniversityCrawlerBase

logger = logging.getLogger(__name__)

_SE_BASE_URL = "https://se.xjtu.edu.cn"
_SE_LIST_URL = f"{_SE_BASE_URL}/jsdw.htm"
_GR_BASE_URL = "http://gr.xjtu.edu.cn"
_AFFILIATION = "西安交通大学软件学院"

_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_INTEREST_SPLIT_RE = re.compile(r"[、，,；;。\n]+")


class XJTUSECrawler(UniversityCrawlerBase):
    """Crawl faculty from XJTU School of Software website."""

    university_id = "xjtu-se"
    display_name = "西安交通大学 - 软件学院"
    crawl_base_url = _SE_BASE_URL

    def crawl_all(self, delay: float = 2.0) -> list[dict]:
        """Crawl list page then enrich each teacher from detail page when possible."""
        session = self._make_session()
        self._solve_challenge(session, _SE_LIST_URL, _SE_BASE_URL)

        try:
            resp = session.get(_SE_LIST_URL, timeout=15)
        except requests.RequestException as exc:
            raise RuntimeError(f"无法连接到目标网站: {exc}") from exc
        if resp.status_code != 200:
            raise RuntimeError(f"列表页请求失败: HTTP {resp.status_code}")

        resp.encoding = "utf-8"
        results = self._parse_list_page(resp.text)

        # gr.xjtu.edu.cn challenge is solved once (on first detail page) if needed.
        gr_challenge_done = False

        for idx, prof in enumerate(results):
            detail_url = prof.get("source_url")
            if not detail_url or detail_url == _SE_LIST_URL:
                continue

            try:
                if detail_url.startswith(_GR_BASE_URL) and not gr_challenge_done:
                    self._solve_challenge(session, detail_url, _GR_BASE_URL)
                    gr_challenge_done = True

                detail_resp = session.get(detail_url, timeout=15)
                if detail_resp.status_code != 200:
                    raise RuntimeError(f"HTTP {detail_resp.status_code}")

                detail_resp.encoding = "utf-8"
                detail_data = self._parse_detail_page(detail_resp.text)
                if detail_data.get("email"):
                    prof["email"] = detail_data["email"]
                if detail_data.get("research_interests"):
                    prof["research_interests"] = detail_data["research_interests"]
                if detail_data.get("homepage"):
                    prof["homepage"] = detail_data["homepage"]
            except Exception as exc:
                # Keep list-page fields; detail-page failure should not break the whole batch.
                logger.warning("解析详情页失败，使用列表页信息继续: %s (%s)", prof.get("name"), exc)

            if delay > 0 and idx < len(results) - 1:
                time.sleep(delay)

        return results

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
                "Referer": _SE_BASE_URL,
            }
        )
        return session

    @staticmethod
    def _solve_challenge(session: requests.Session, url: str, base_url: str) -> None:
        """Solve JS challenge on a given site if challenge markers are present."""
        try:
            response = session.get(url, timeout=15)
        except requests.RequestException as exc:
            raise RuntimeError(f"无法连接到目标网站: {exc}") from exc

        body = response.text
        cid_match = re.search(r'challengeId\s*=\s*"([^"]+)"', body)
        ans_match = re.search(r"\bvar\s+answer\s*=\s*(\d+)", body)
        if not cid_match:
            return
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
            challenge_resp = session.post(
                f"{base_url}/dynamic_challenge",
                json=payload,
                timeout=10,
            )
            data = challenge_resp.json()
            if not data.get("success"):
                raise RuntimeError(f"JS 挑战失败: {data}")
        except (requests.RequestException, ValueError) as exc:
            raise RuntimeError(f"JS 挑战请求失败: {exc}") from exc

    @staticmethod
    def _normalize_name(raw_name: str) -> str:
        """Normalize Chinese names like '王 伟' / '郑  帅' to compact form."""
        return re.sub(r"\s+", "", raw_name or "").strip()

    @staticmethod
    def _parse_list_page(html: str) -> list[dict]:
        """Parse faculty entries from software school list page."""
        soup = BeautifulSoup(html, "html.parser")
        results: list[dict] = []

        teacher_container = soup.select_one("div.teacher")
        if not teacher_container:
            return results

        for sub in teacher_container.select("div.teaSub"):
            for a in sub.select("ul.clearfix li a"):
                raw_name = a.get_text(strip=True)
                name = XJTUSECrawler._normalize_name(raw_name)
                if not name:
                    continue

                href = (a.get("href") or "").strip()
                detail_url = urljoin(_SE_BASE_URL + "/", href) if href else None

                results.append(
                    {
                        "name": name,
                        "affiliation": _AFFILIATION,
                        "email": None,
                        "homepage": detail_url,
                        "research_interests": [],
                        "source_url": detail_url or _SE_LIST_URL,
                    }
                )

        return results

    @staticmethod
    def _parse_detail_page(html: str) -> dict:
        """Extract email and research interests from a generic profile page."""
        soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text("\n", strip=True)

        email_match = _EMAIL_RE.search(text)
        email: Optional[str] = email_match.group(0) if email_match else None

        interests: list[str] = []
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        for line in lines:
            if any(key in line for key in ("研究方向", "研究兴趣", "科研方向")):
                cleaned = line
                for key in ("研究方向", "研究兴趣", "科研方向", "：", ":"):
                    cleaned = cleaned.replace(key, " ")
                parts = [p.strip() for p in _INTEREST_SPLIT_RE.split(cleaned) if p.strip()]
                interests.extend(parts)

        # Preserve order while removing duplicates
        deduped_interests = list(dict.fromkeys(interests))

        return {
            "email": email,
            "research_interests": deduped_interests,
            "homepage": None,
        }
