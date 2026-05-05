import json
import pytest
import requests
from unittest.mock import MagicMock, patch
from ratings.ratings import FaRatings, _get_ftoken, SEARCH_URL, FILM_URL


FILM_URL_FULL = 'https://www.filmaffinity.com/es/film891160.html'
SEARCH_HTML = f"""
<html><body>
  <div class="se-it">
    <a href="{FILM_URL_FULL}">Hannibal</a>
  </div>
</body></html>
"""
FILM_HTML = """
<html><body>
  <h1 id="main-title"><span itemprop="name">Hannibal</span></h1>
  <div id="movie-rat-avg">7,4</div>
</body></html>
"""
FA_MAIN_HTML = f'<html><script>var ftoken = "{"a" * 64}";</script></html>'


def make_resp(text='', status=200):
    resp = MagicMock(status_code=status)
    resp.raise_for_status = MagicMock()
    resp.content = text.encode()
    return resp


def make_session(search_html=SEARCH_HTML, film_html=FILM_HTML):
    session = MagicMock()
    session.get.side_effect = [make_resp(search_html), make_resp(film_html)]
    return session


def make_fa(session):
    fa = FaRatings.__new__(FaRatings)
    fa.session = session
    fa.ftoken = "a" * 64
    return fa


class TestGetFtoken:
    def test_extracts_token_from_page(self):
        token = "b" * 64
        session = MagicMock()
        session.get.return_value = MagicMock(text=f'var ftoken = "{token}";')
        assert _get_ftoken(session) == token

    def test_returns_none_on_request_error(self):
        session = MagicMock()
        session.get.side_effect = requests.RequestException("timeout")
        assert _get_ftoken(session) is None

    def test_returns_none_when_token_not_in_page(self):
        session = MagicMock()
        session.get.return_value = MagicMock(text="<html>no token here</html>")
        assert _get_ftoken(session) is None


class TestGetRating:
    def test_returns_title_and_rating(self):
        fa = make_fa(make_session())
        found_title, rating, film_url = fa.get_rating("Hannibal")
        assert found_title == "Hannibal"
        assert rating == "7,4"
        assert film_url == FILM_URL_FULL

    def test_searches_correct_url(self):
        fa = make_fa(make_session())
        fa.get_rating("Hannibal")
        fa.session.get.assert_any_call(SEARCH_URL + "Hannibal", timeout=10)

    def test_not_found_when_no_search_results(self):
        fa = make_fa(make_session(search_html='<html><body></body></html>'))
        # only one GET call (no film page fetch)
        fa.session.get.side_effect = [make_resp('<html><body></body></html>')]
        found_title, rating, film_url = fa.get_rating("xyzzy")
        assert found_title == "Not Found"
        assert rating == "00"
        assert film_url is None

    def test_not_found_on_request_error(self):
        session = MagicMock()
        session.get.side_effect = requests.RequestException("network error")
        fa = make_fa(session)
        found_title, rating, film_url = fa.get_rating("Hannibal")
        assert found_title == "Not Found"
        assert rating == "00"

    def test_rating_defaults_to_zero_when_missing_from_film_page(self):
        html = '<html><body><h1 id="main-title"><span itemprop="name">Unknown</span></h1></body></html>'
        fa = make_fa(make_session(film_html=html))
        _, rating, _ = fa.get_rating("Unknown")
        assert rating == "00"


@pytest.mark.integration
class TestIntegration:
    """Hits the real FilmAffinity site. Run with: pytest -m integration"""

    @pytest.fixture(scope="class")
    def fa(self):
        instance = FaRatings.__new__(FaRatings)
        instance.session = requests.Session()
        instance.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:138.0) Gecko/20100101 Firefox/138.0"
        })
        instance.ftoken = None
        return instance

    def test_known_film_returns_rating(self, fa):
        """Hannibal TV series (film891160) has a stable 7.x rating."""
        found_title, rating, film_url = fa.get_rating("Hannibal")
        assert found_title != "Not Found", f"Expected a film, got Not Found"
        assert rating != "00", f"Expected a rating, got 00"
        assert float(rating.replace(",", ".")) > 0
        assert "filmaffinity.com" in film_url
        print(f"\n  {found_title}: {rating} — {film_url}")

    def test_unknown_title_returns_not_found(self, fa):
        found_title, rating, film_url = fa.get_rating("xyzzy_no_such_film_abc123")
        assert found_title == "Not Found"
        assert rating == "00"
        assert film_url is None
