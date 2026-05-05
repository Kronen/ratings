import argparse
import configparser
import logging
import os

from ratings.ratings import FaRatings

CONFIG_FILE = os.path.expanduser('~/.faratings.cfg')
CONFIG_SECTION = 'faratings'

logging.basicConfig(filename='errors.log', level=logging.DEBUG)


def load_config_path():
    cfg = configparser.ConfigParser()
    cfg.read(CONFIG_FILE)
    return cfg.get(CONFIG_SECTION, 'path', fallback=None)


def save_config_path(path):
    cfg = configparser.ConfigParser()
    cfg.read(CONFIG_FILE)
    if CONFIG_SECTION not in cfg:
        cfg[CONFIG_SECTION] = {}
    cfg[CONFIG_SECTION]['path'] = path
    with open(CONFIG_FILE, 'w') as f:
        cfg.write(f)


def resolve_path(args):
    if args.path:
        if args.save:
            save_config_path(args.path)
            print(f"-> Saved path to {CONFIG_FILE}")
        return args.path
    stored = load_config_path()
    if stored:
        print(f"-> Using saved path: {stored}")
        return stored
    cwd = os.getcwd()
    print(f"-> No path given, using current directory: {cwd}")
    return cwd


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Fetch FilmAffinity ratings for local video files.')
    parser.add_argument('path', nargs='?', help='Folder containing video files')
    parser.add_argument('--save', action='store_true', help=f'Save path to {CONFIG_FILE}')
    args = parser.parse_args()

    path = resolve_path(args)
    FaRatings(path).write_ratings()
