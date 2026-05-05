# FaRatings

Overlay [FilmAffinity](https://www.filmaffinity.com) ratings directly on Netflix title cards — no manual lookups needed.

## Firefox Extension

The extension injects a small rating badge onto every Netflix title card as you browse. Badges are color-coded by score and link directly to the FilmAffinity film page.

| Badge color | Rating |
|-------------|--------|
| Green | ≥ 7.0 |
| Yellow | 5.0 – 6.9 |
| Red | < 5.0 |
| Grey | Not found |

### Installation

1. Clone this repo.
2. Open Firefox and go to `about:debugging` → **This Firefox** → **Load Temporary Add-on**.
3. Select `extension/manifest.json`.
4. Browse to [netflix.com](https://www.netflix.com) — badges appear automatically.

> **Note:** Temporary add-ons are removed when Firefox restarts. For a persistent install, the extension needs to be signed by Mozilla.

### How it works

- A `MutationObserver` watches for Netflix title cards entering the DOM.
- An `IntersectionObserver` queues only visible cards to avoid flooding requests.
- The background service worker calls FilmAffinity's autocomplete API, resolves the film ID, fetches the film page, and caches the result in `browser.storage.local`.
- Subsequent views of the same title are served instantly from cache.

---

## CLI Tool

A Python script that scans a local folder of video files, guesses titles with [guessit](https://guessit.io), fetches FilmAffinity ratings, and writes a CSV sorted by rating.

### Usage

```bash
pip install -r requirements.txt
```

```bash
# Run on a specific folder
python main.py /path/to/movies

# Run and save that folder for future runs
python main.py /path/to/movies --save

# Run using the saved path (or current directory if none saved)
python main.py
```

The saved path is stored in `~/.faratings.cfg`.

Output: `film_ratings.csv` with columns `rating`, `guessed_title`, `found_title`, `film_url`, `file`.

### Tests

```bash
pytest                   # unit tests only
pytest --integration     # includes live FilmAffinity requests
```

---

## Acknowledgements

Rating data sourced from [FilmAffinity](https://www.filmaffinity.com).  
CLI dependencies: [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup), [requests](https://github.com/psf/requests), [guessit](https://guessit.io), [progressbar2](https://progressbar-2.readthedocs.io/).
