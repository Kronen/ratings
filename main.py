import logging

from ratings.ratings import FaRatings


logging.basicConfig(filename='errors.log', level=logging.DEBUG)
LOG = logging.getLogger('ratings')


if __name__ == '__main__':
    path = r'C:\Users\Kronen\Descargas\Torrents'  # EDIT PATH TO MOVIES FOLDER
    ratings = FaRatings(path)
    ratings.write_ratings()
