import os
import requests
import logging

from csv import DictWriter
from bs4 import BeautifulSoup
from guessit import guessit
from progressbar import ProgressBar, UnknownLength


EXTENSIONS = ('avi', 'mkv', 'mpg', 'mp4', 'divx', 'iso')
SEARCH_URL = 'https://www.filmaffinity.com/es/advsearch.php?stext='

LOG = logging.getLogger(__name__)


class Ratings:

    def __init__(self, path):
        self.ratings = self.load_ratings(path)
        self.path = path

    def get_rating(self, film_name):
        response = requests.get(SEARCH_URL + film_name)
        """Avoids ISO-8859-1 as default when character encoding is not specified in the
        Content-Type header field.
        When None is specified as encoding for BeautifulSoup it will try to guess the correct
        encoding."""
        enc = response.encoding if 'charset' in response.headers['Content-Type'] else None
        soup = BeautifulSoup(response.content, 'html.parser', from_encoding=enc)
        try:
            title = soup.find('div', class_='mc-poster').a['title']
            rating = soup.find('div', class_='avgrat-box').text
        except AttributeError:
            return 'Not Found', '00'
        return title, rating

    def film_files(self, path):
        for root, dirs, files in os.walk(path, topdown=True):
            for filename in files:
                if filename.endswith(EXTENSIONS):
                    yield filename

    def load_ratings(self, path):
        self.ratings = []
        bar = ProgressBar(max_value=UnknownLength)
        count = 0

        for file in self.film_files(path):
            guessed_data = guessit(file)
            guessed_title = guessed_data.get('title', '')
            if guessed_title:
                found_title, rating = self.get_rating(guessed_title)
            else:
                found_title, rating = 'Not Guessed', '00'

            self.ratings.append({'file': file,
                                 'guessed_title': guessed_title,
                                 'found_title': found_title,
                                 'rating': rating})
            bar.update(count)
            count += 1

        ratings = sorted(self.ratings, key=lambda k: k['rating'], reverse=True)
        return ratings

    def write_ratings(self, ratings_file='film_ratings.csv'):
        with open(ratings_file, 'w', encoding="utf8") as csvfile:
            fieldnames = ['rating', 'guessed_title', 'found_title', 'file']
            writer = DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for film in self.ratings:
                try:
                    writer.writerow(film)
                except UnicodeEncodeError as uee:
                    logging.error('Error trying to write the found title of {}'
                                  .format(film['file']))
                    logging.error(uee)
