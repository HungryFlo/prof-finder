"""Unit tests for the XJTU CS crawler (no real network requests).

Covers: card parsing, list-page parsing, JS challenge solving,
        crawl_all (single + multi-page), and the crawler registry.
"""

from unittest.mock import MagicMock, patch, call

import pytest

from prof_finder.crawler.universities.xjtu_cs import XJTUCSCrawler
from prof_finder.crawler.universities.registry import (
    REGISTRY,
    get_crawler,
    get_crawler_info_list,
)


# ---------------------------------------------------------------------------
# Sample HTML fixtures
# ---------------------------------------------------------------------------

# Minimal challenge page HTML
CHALLENGE_HTML = """
<html><body>
<script>
  var challengeId = "testChallenge123";
  var answer = 42;
</script>
</body></html>
"""

# One professor card on the real list page structure
PROF_CARD_HTML = """
<div class="clearfix per">
  <div class="person-photo">
    <a href="http://www.xjtu.edu.cn/jsnr.jsp?wbwbxjtuteacherid=457">
      <img alt="" src="/photo.jpg"/>
    </a>
  </div>
  <div class="person-produce clearfix">
    <div class="person-produce-top clearfix">
      <a class="more" href="http://www.xjtu.edu.cn/jsnr.jsp?wbwbxjtuteacherid=457">
        了解详细<span></span>
      </a>
      <h3>董小社  (教授)</h3>
    </div>
    <div class="person-produce-content">
      <div class="person-produce-content-left">
        <ul>
          <li>办公室：西一楼A413</li>
          <li>电话：029-82663951-801</li>
          <li>邮箱：xsdong@xjtu.edu.cn</li>
          <li>博士生导师</li>
        </ul>
      </div>
      <div class="person-produce-content-right">
        <h4>研究方向：</h4>
        <p>高性能计算机体系结构及其核心软件、并行算法与编程模型、分布式处理。</p>
      </div>
    </div>
  </div>
</div>
"""

# Two-card page
TWO_PROFS_HTML = f"""
<html><head><title>教授</title></head><body>
{PROF_CARD_HTML}
<div class="clearfix per">
  <div class="person-photo"></div>
  <div class="person-produce clearfix">
    <div class="person-produce-top clearfix">
      <a class="more" href="http://www.xjtu.edu.cn/jsnr.jsp?wbwbxjtuteacherid=999">了解详细</a>
      <h3>李辰  (教授)</h3>
    </div>
    <div class="person-produce-content">
      <div class="person-produce-content-left">
        <ul>
          <li>办公室：彭康楼223</li>
          <li>电话：</li>
          <li>邮箱：cli@xjtu.edu.cn</li>
          <li>博士生导师</li>
        </ul>
      </div>
      <div class="person-produce-content-right">
        <h4>研究方向：</h4>
        <p>自然语言处理、语义理解、生物医学大数据。</p>
      </div>
    </div>
  </div>
</div>
</body></html>
"""

# Card with missing email and no research interests paragraph
MINIMAL_CARD_HTML = """
<html><body>
<div class="clearfix per">
  <div class="person-produce clearfix">
    <div class="person-produce-top clearfix">
      <a class="more" href="http://example.com/prof">了解详细</a>
      <h3>张三（副教授）</h3>
    </div>
    <div class="person-produce-content">
      <div class="person-produce-content-left"><ul><li>办公室：A101</li></ul></div>
      <div class="person-produce-content-right"><h4>研究方向：</h4></div>
    </div>
  </div>
</div>
</body></html>
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_mock_response(html: str, status_code: int = 200) -> MagicMock:
    mock = MagicMock()
    mock.status_code = status_code
    mock.text = html
    mock.encoding = "utf-8"
    return mock


def _make_challenge_resp() -> MagicMock:
    return _make_mock_response(CHALLENGE_HTML)


def _make_content_resp(html: str) -> MagicMock:
    return _make_mock_response(html)


# ---------------------------------------------------------------------------
# Tests: _parse_card
# ---------------------------------------------------------------------------

class TestParseCard:
    def test_parses_name_strips_title(self):
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(PROF_CARD_HTML, "html.parser")
        card = soup.find("div", class_="per")
        result = XJTUCSCrawler._parse_card(card)
        assert result["name"] == "董小社"

    def test_parses_email(self):
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(PROF_CARD_HTML, "html.parser")
        card = soup.find("div", class_="per")
        result = XJTUCSCrawler._parse_card(card)
        assert result["email"] == "xsdong@xjtu.edu.cn"

    def test_parses_research_interests(self):
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(PROF_CARD_HTML, "html.parser")
        card = soup.find("div", class_="per")
        result = XJTUCSCrawler._parse_card(card)
        assert "高性能计算机体系结构及其核心软件" in result["research_interests"]
        assert "并行算法与编程模型" in result["research_interests"]

    def test_affiliation_is_xjtu(self):
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(PROF_CARD_HTML, "html.parser")
        card = soup.find("div", class_="per")
        result = XJTUCSCrawler._parse_card(card)
        assert result["affiliation"] == "西安交通大学计算机科学与技术学院"

    def test_source_url_extracted(self):
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(PROF_CARD_HTML, "html.parser")
        card = soup.find("div", class_="per")
        result = XJTUCSCrawler._parse_card(card)
        assert "xjtuteacherid=457" in result["source_url"]

    def test_missing_email_returns_none(self):
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(MINIMAL_CARD_HTML, "html.parser")
        card = soup.find("div", class_="per")
        result = XJTUCSCrawler._parse_card(card)
        assert result["email"] is None

    def test_missing_research_interests_returns_empty_list(self):
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(MINIMAL_CARD_HTML, "html.parser")
        card = soup.find("div", class_="per")
        result = XJTUCSCrawler._parse_card(card)
        assert result["research_interests"] == []

    def test_title_in_full_width_parens_stripped(self):
        from bs4 import BeautifulSoup

        html = """<div class="clearfix per">
          <div class="person-produce clearfix">
            <div class="person-produce-top"><a class="more" href="#">了解详细</a><h3>张三（副教授）</h3></div>
            <div class="person-produce-content">
              <div class="person-produce-content-left"><ul></ul></div>
              <div class="person-produce-content-right"></div>
            </div>
          </div></div>"""
        soup = BeautifulSoup(html, "html.parser")
        card = soup.find("div", class_="per")
        result = XJTUCSCrawler._parse_card(card)
        assert result["name"] == "张三"


# ---------------------------------------------------------------------------
# Tests: _parse_list_page
# ---------------------------------------------------------------------------

class TestParseListPage:
    def test_returns_correct_count(self):
        results = XJTUCSCrawler._parse_list_page(TWO_PROFS_HTML)
        assert len(results) == 2

    def test_all_required_keys_present(self):
        results = XJTUCSCrawler._parse_list_page(TWO_PROFS_HTML)
        for r in results:
            for key in ("name", "affiliation", "email", "homepage", "research_interests", "source_url"):
                assert key in r

    def test_empty_page_returns_empty_list(self):
        results = XJTUCSCrawler._parse_list_page("<html><body></body></html>")
        assert results == []


# ---------------------------------------------------------------------------
# Tests: _solve_challenge
# ---------------------------------------------------------------------------

class TestSolveChallenge:
    def test_solves_challenge_and_sets_cookie(self):
        session = MagicMock()
        session.get.return_value = _make_challenge_resp()
        session.post.return_value = MagicMock(
            json=lambda: {"success": True, "client_id": "cid_abc"}
        )

        XJTUCSCrawler._solve_challenge(session, "http://example.com")

        session.post.assert_called_once()
        call_kwargs = session.post.call_args
        payload = call_kwargs.kwargs.get("json") or call_kwargs.args[1]
        assert payload["challenge_id"] == "testChallenge123"
        assert payload["answer"] == 42

    def test_no_challenge_skips_post(self):
        session = MagicMock()
        session.get.return_value = _make_mock_response("<html><body>normal page</body></html>")

        XJTUCSCrawler._solve_challenge(session, "http://example.com")

        session.post.assert_not_called()

    def test_failed_challenge_raises_runtime_error(self):
        session = MagicMock()
        session.get.return_value = _make_challenge_resp()
        session.post.return_value = MagicMock(
            json=lambda: {"success": False, "message": "Invalid"}
        )

        with pytest.raises(RuntimeError, match="JS 挑战失败"):
            XJTUCSCrawler._solve_challenge(session, "http://example.com")


# ---------------------------------------------------------------------------
# Tests: crawl_all (integration-style, mocked HTTP)
# ---------------------------------------------------------------------------

class TestCrawlAll:
    def test_returns_professors_from_all_categories(self):
        """crawl_all iterates over all 5 category pages and merges results."""
        crawler = XJTUCSCrawler()
        # Each of the 5 category pages returns TWO_PROFS_HTML (2 professors each)
        with patch.object(XJTUCSCrawler, "_solve_challenge", return_value=None):
            with patch("requests.Session.get", return_value=_make_content_resp(TWO_PROFS_HTML)):
                results = crawler.crawl_all(delay=0)
        # 5 categories × 2 professors = 10
        assert len(results) == 10

    def test_skips_failed_category_page(self):
        """A non-200 response for a category page is skipped, others continue."""
        from prof_finder.crawler.universities.xjtu_cs import _CATEGORY_PAGES

        crawler = XJTUCSCrawler()
        responses = []
        for i, _ in enumerate(_CATEGORY_PAGES):
            # Make the second category return 503, all others 200
            code = 503 if i == 1 else 200
            responses.append(_make_mock_response(TWO_PROFS_HTML if code == 200 else "", code))

        with patch.object(XJTUCSCrawler, "_solve_challenge", return_value=None):
            with patch("requests.Session.get", side_effect=responses):
                results = crawler.crawl_all(delay=0)

        # 4 successful pages × 2 professors each = 8
        assert len(results) == 8

    def test_challenge_solved_only_once(self):
        """_solve_challenge is called exactly once regardless of category count."""
        crawler = XJTUCSCrawler()
        with patch.object(XJTUCSCrawler, "_solve_challenge", return_value=None) as mock_solve:
            with patch("requests.Session.get", return_value=_make_content_resp(TWO_PROFS_HTML)):
                crawler.crawl_all(delay=0)
        mock_solve.assert_called_once()

    def test_raises_on_first_page_connection_error(self):
        """If the first page raises, crawl_all propagates the RuntimeError."""
        crawler = XJTUCSCrawler()

        def _bad_solve(session, url):
            raise RuntimeError("无法连接到目标网站: connection refused")

        with patch.object(XJTUCSCrawler, "_solve_challenge", side_effect=_bad_solve):
            with pytest.raises(RuntimeError, match="无法连接"):
                crawler.crawl_all(delay=0)


# ---------------------------------------------------------------------------
# Tests: registry
# ---------------------------------------------------------------------------

class TestRegistry:
    def test_xjtu_cs_registered(self):
        assert "xjtu-cs" in REGISTRY

    def test_get_crawler_returns_instance(self):
        crawler = get_crawler("xjtu-cs")
        assert isinstance(crawler, XJTUCSCrawler)

    def test_get_crawler_unknown_raises_key_error(self):
        with pytest.raises(KeyError):
            get_crawler("non-existent-id")

    def test_crawler_info_list_contains_xjtu(self):
        info_list = get_crawler_info_list()
        ids = [item["university_id"] for item in info_list]
        assert "xjtu-cs" in ids

    def test_crawler_info_has_display_name(self):
        info_list = get_crawler_info_list()
        xjtu = next(i for i in info_list if i["university_id"] == "xjtu-cs")
        assert "西安交通大学" in xjtu["display_name"]
