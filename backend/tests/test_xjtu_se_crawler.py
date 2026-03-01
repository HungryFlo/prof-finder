"""Unit tests for XJTU Software School crawler (no real network requests)."""

from unittest.mock import MagicMock, patch

import pytest

from prof_finder.crawler.universities.registry import (
    REGISTRY,
    get_crawler,
    get_crawler_info_list,
)
from prof_finder.crawler.universities.xjtu_se import XJTUSECrawler

CHALLENGE_HTML = """
<html><body>
<script>
  var challengeId = "challengeSE";
  var answer = 88;
</script>
</body></html>
"""

LIST_HTML = """
<html><body>
  <div class="teacher">
    <div class="teaSub">
      <h2><p>教授</p></h2>
      <ul class="clearfix">
        <li><a href="http://gr.xjtu.edu.cn/web/wei.wang">王 伟</a></li>
        <li><a>郑  帅</a></li>
      </ul>
    </div>
    <div class="teaSub">
      <h2><p>副教授</p></h2>
      <ul class="clearfix">
        <li><a href="/profiles/li.chen">李 晨</a></li>
      </ul>
    </div>
  </div>
</body></html>
"""

DETAIL_HTML = """
<html><body>
  <div>邮箱：weiwang@xjtu.edu.cn</div>
  <div>研究方向：软件测试、程序分析；大模型应用。</div>
</body></html>
"""


def _make_mock_response(html: str, status_code: int = 200) -> MagicMock:
    mock = MagicMock()
    mock.status_code = status_code
    mock.text = html
    mock.encoding = "utf-8"
    return mock


class TestParseListPage:
    def test_parse_count(self):
        results = XJTUSECrawler._parse_list_page(LIST_HTML)
        assert len(results) == 3

    def test_name_is_normalized(self):
        results = XJTUSECrawler._parse_list_page(LIST_HTML)
        names = [r["name"] for r in results]
        assert "王伟" in names
        assert "郑帅" in names
        assert "李晨" in names

    def test_missing_href_uses_list_url(self):
        results = XJTUSECrawler._parse_list_page(LIST_HTML)
        prof = next(r for r in results if r["name"] == "郑帅")
        assert prof["source_url"].endswith("/jsdw.htm")
        assert prof["homepage"] is None
        assert prof["email"] is None
        assert prof["research_interests"] == []

    def test_relative_href_is_joined(self):
        results = XJTUSECrawler._parse_list_page(LIST_HTML)
        prof = next(r for r in results if r["name"] == "李晨")
        assert prof["source_url"] == "https://se.xjtu.edu.cn/profiles/li.chen"


class TestParseDetailPage:
    def test_extracts_email_and_interests(self):
        detail = XJTUSECrawler._parse_detail_page(DETAIL_HTML)
        assert detail["email"] == "weiwang@xjtu.edu.cn"
        assert "软件测试" in detail["research_interests"]
        assert "程序分析" in detail["research_interests"]
        assert "大模型应用" in detail["research_interests"]


class TestSolveChallenge:
    def test_solves_when_challenge_exists(self):
        session = MagicMock()
        session.get.return_value = _make_mock_response(CHALLENGE_HTML)
        session.post.return_value = MagicMock(
            json=lambda: {"success": True, "client_id": "cid_abc"}
        )

        XJTUSECrawler._solve_challenge(session, "https://se.xjtu.edu.cn/jsdw.htm", "https://se.xjtu.edu.cn")

        session.post.assert_called_once()
        payload = session.post.call_args.kwargs["json"]
        assert payload["challenge_id"] == "challengeSE"
        assert payload["answer"] == 88

    def test_skips_when_no_challenge(self):
        session = MagicMock()
        session.get.return_value = _make_mock_response("<html><body>ok</body></html>")

        XJTUSECrawler._solve_challenge(session, "https://se.xjtu.edu.cn/jsdw.htm", "https://se.xjtu.edu.cn")

        session.post.assert_not_called()

    def test_raises_on_failed_challenge(self):
        session = MagicMock()
        session.get.return_value = _make_mock_response(CHALLENGE_HTML)
        session.post.return_value = MagicMock(json=lambda: {"success": False})

        with pytest.raises(RuntimeError, match="JS 挑战失败"):
            XJTUSECrawler._solve_challenge(
                session, "https://se.xjtu.edu.cn/jsdw.htm", "https://se.xjtu.edu.cn"
            )


class TestCrawlAll:
    def test_enriches_detail_data_and_handles_missing_href(self):
        crawler = XJTUSECrawler()

        # get() call sequence:
        # 1) solve se challenge -> challenge page
        # 2) fetch se list page -> list html
        # 3) solve gr challenge for first detail -> challenge page
        # 4) fetch first detail page -> detail html
        # 5) fetch second detail page (relative se url) -> non-200 to verify fallback
        responses = [
            _make_mock_response(CHALLENGE_HTML),
            _make_mock_response(LIST_HTML),
            _make_mock_response(CHALLENGE_HTML),
            _make_mock_response(DETAIL_HTML),
            _make_mock_response("", 502),
        ]
        post_resp = MagicMock(json=lambda: {"success": True, "client_id": "cid_ok"})

        with patch("requests.Session.get", side_effect=responses):
            with patch("requests.Session.post", return_value=post_resp):
                results = crawler.crawl_all(delay=0)

        assert len(results) == 3
        wang = next(r for r in results if r["name"] == "王伟")
        assert wang["email"] == "weiwang@xjtu.edu.cn"
        assert "软件测试" in wang["research_interests"]

        zheng = next(r for r in results if r["name"] == "郑帅")
        assert zheng["source_url"].endswith("/jsdw.htm")
        assert zheng["email"] is None

        li = next(r for r in results if r["name"] == "李晨")
        # Detail page 502 should keep list-page fallback
        assert li["email"] is None
        assert li["research_interests"] == []

    def test_raises_when_list_page_non_200(self):
        crawler = XJTUSECrawler()
        responses = [
            _make_mock_response(CHALLENGE_HTML),  # for solve challenge
            _make_mock_response("", 503),         # list page fetch
        ]
        with patch("requests.Session.get", side_effect=responses):
            with patch(
                "requests.Session.post",
                return_value=MagicMock(json=lambda: {"success": True, "client_id": "cid_ok"}),
            ):
                with pytest.raises(RuntimeError, match="列表页请求失败"):
                    crawler.crawl_all(delay=0)


class TestRegistry:
    def test_xjtu_se_registered(self):
        assert "xjtu-se" in REGISTRY

    def test_get_crawler_returns_se_instance(self):
        crawler = get_crawler("xjtu-se")
        assert isinstance(crawler, XJTUSECrawler)

    def test_crawler_info_contains_se(self):
        info_list = get_crawler_info_list()
        se = next(i for i in info_list if i["university_id"] == "xjtu-se")
        assert "软件学院" in se["display_name"]
