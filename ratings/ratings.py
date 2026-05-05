import os
import re
import time
import logging

from csv import DictWriter
from bs4 import BeautifulSoup
from guessit import guessit
from progressbar import ProgressBar, UnknownLength
import requests


EXTENSIONS = ('avi', 'mkv', 'mpg', 'mp4', 'divx', 'iso')
FA_MAIN = 'https://www.filmaffinity.com/es/main.html'
AC_URL = 'https://www.filmaffinity.com/es/search-ac2.w2.ajax.php?action=searchTerm'
SEARCH_URL = 'https://www.filmaffinity.com/es/search.php?stext='
FILM_URL = 'https://www.filmaffinity.com/es/film{}.html'
REQUEST_DELAY = 0.4  # seconds between requests

LOG = logging.getLogger(__name__)


def _get_ftoken(session):
    try:
        resp = session.get(FA_MAIN, timeout=10)
        match = re.search(r'[\'\"]([\da-f]{64})[\'\"]', resp.text)
        if match:
            return match.group(1)
    except requests.RequestException as e:
        LOG.warning('Could not fetch ftoken: %s', e)
    return None


class FaRatings:

    def __init__(self, path):
        self.path = path
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'Mozilla/5.0'})
        self.ftoken = _get_ftoken(self.session)
        self.ratings = self.load_ratings()

    def get_rating(self, film_name):
        try:
            search_resp = self.session.get(SEARCH_URL + film_name, timeout=10)
            search_resp.raise_for_status()

            search_soup = BeautifulSoup(search_resp.content, 'html.parser')
            film_links = search_soup.select('.se-it a[href*="/es/film"]')
            if not film_links:
                return 'Not Found', '00', None

            for film_link in film_links:
                film_url = film_link['href']
                time.sleep(REQUEST_DELAY)
                film_resp = self.session.get(film_url, timeout=10)
                film_resp.raise_for_status()

                soup = BeautifulSoup(film_resp.content, 'html.parser')
                rating_el = soup.select_one('#movie-rat-avg')
                if not rating_el:
                    continue

                title_el = soup.select_one('h1#main-title span[itemprop="name"]')
                return (
                    title_el.text.strip() if title_el else 'Not Found',
                    rating_el.text.strip(),
                    film_url,
                )

            return 'Not Found', '00', None
        except (requests.RequestException, ValueError, KeyError) as e:
            LOG.error('Error fetching rating for %s: %s', film_name, e)
            return 'Not Found', '00', None

    def film_files(self):
        for root, dirs, files in os.walk(self.path, topdown=True):
            for filename in files:
                if filename.endswith(EXTENSIONS):
                    yield filename

    def load_ratings(self):
        ratings = []
        bar = ProgressBar(max_value=UnknownLength)
        count = 0

        for file in self.film_files():
            guessed_title = guessit(file).get('title', '')
            if guessed_title:
                found_title, rating, film_url = self.get_rating(guessed_title)
            else:
                found_title, rating, film_url = 'Not Guessed', '00', None

            ratings.append({
                'file': file,
                'guessed_title': guessed_title,
                'found_title': found_title,
                'rating': rating,
                'film_url': film_url or '',
            })
            bar.update(count)
            count += 1
            time.sleep(REQUEST_DELAY)

        return sorted(ratings, key=lambda k: k['rating'], reverse=True)

    def write_ratings(self, ratings_file='film_ratings.csv'):
        with open(ratings_file, 'w', encoding='utf-8', newline='') as csv_file:
            fieldnames = ['rating', 'guessed_title', 'found_title', 'film_url', 'file']
            writer = DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()
            for film in self.ratings:
                try:
                    writer.writerow(film)
                except UnicodeEncodeError as e:
                    LOG.error('Error writing %s: %s', film['file'], e)
