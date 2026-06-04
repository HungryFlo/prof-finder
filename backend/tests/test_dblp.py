"""Tests for DBLP client."""

from unittest.mock import MagicMock, patch

import pytest
import requests

from prof_finder.crawler.dblp import DblpClient, extract_dblp_pid_from_url

SAMPLE_SEARCH_JSON = {
    "result": {
        "hits": {
            "hit": {
                "@score": "3",
                "info": {
                    "author": "Yann LeCun",
                    "url": "https://dblp.org/pid/l/YannLeCun",
                    "notes": {
                        "note": {"@type": "affiliation", "text": "New York University"},
                    },
                },
            }
        }
    }
}

SAMPLE_PID_XML = b"""<?xml version="1.0"?>
<dblpperson name="Yann LeCun" pid="l/YannLeCun" n="2">
<person key="homepages/l/YannLeCun">
<note type="affiliation">NYU</note>
</person>
<r><article key="journals/corr/abs-2601-00844">
<title>Test Paper</title>
<year>2026</year>
<author>Yann LeCun</author>
<journal>CoRR</journal>
</article></r>
</dblpperson>
"""


def test_extract_pid_from_url():
    assert extract_dblp_pid_from_url("https://dblp.org/pid/l/YannLeCun.html") == "l/YannLeCun"
    assert extract_dblp_pid_from_url("l/YannLeCun") == "l/YannLeCun"


def test_search_author_single_hit():
    client = DblpClient(request_delay=0)
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = SAMPLE_SEARCH_JSON
    with patch.object(client._session, "get", return_value=mock_resp):
        results = client.search_author("Yann LeCun", limit=5)
    assert len(results) == 1
    assert results[0]["pid"] == "l/YannLeCun"
    assert results[0]["name"] == "Yann LeCun"


def test_search_author_retries_on_timeout():
    client = DblpClient(request_delay=0)
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = SAMPLE_SEARCH_JSON
    with patch.object(client._session, "get") as mock_get:
        mock_get.side_effect = [
            requests.Timeout("read timed out"),
            mock_resp,
        ]
        with patch("prof_finder.crawler.dblp.time.sleep"):
            results = client.search_author("Yann LeCun", limit=5)
    assert len(results) == 1
    assert mock_get.call_count == 2


def test_get_author_parses_xml():
    client = DblpClient(request_delay=0)
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.content = SAMPLE_PID_XML
    with patch.object(client._session, "get", return_value=mock_resp):
        data = client.get_author("l/YannLeCun")
    assert data is not None
    assert data["name"] == "Yann LeCun"
    assert len(data["publications"]) == 1
    assert data["publications"][0]["title"] == "Test Paper"
    assert data["publications"][0]["source"] == "dblp"
