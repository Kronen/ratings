import logging

from ratings.ratings import FaRatings


logging.basicConfig(filename='errors.log', level=logging.DEBUG)
LOG = logging.getLogger('ratings')


if __name__ == '__main__':
    path = ''
    if not path:
        print("-> Set Path to movies folder in main.py")
    ratings = FaRatings(path)
    ratings.write_ratings()
