import logging

from ratings.ratings import Ratings


logging.basicConfig(filename='errors.log', level=logging.DEBUG)
LOG = logging.getLogger('ratings')


if __name__ == '__main__':
    path = ''  # EDIT PATH TO MOVIES FOLDER
    ratings = Ratings(path)
    ratings.write_ratings()
