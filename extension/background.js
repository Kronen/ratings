const AC_URL = 'https://www.filmaffinity.com/es/search-ac2.w2.ajax.php?action=searchTerm';
const FA_MAIN = 'https://www.filmaffinity.com/es/main.html';
const CACHE_PREFIX = 'fa_';
const REQUEST_DELAY_MS = 400;
let ftoken = null;

const queue = [];
let processing = false;

browser.runtime.onMessage.addListener((message) => {
  if (message.type === 'GET_RATING') {
    return getRating(message.title);
  }
});

function getRating(title) {
  return new Promise((resolve) => {
    queue.push({ title, resolve });
    drainQueue();
  });
}

async function drainQueue() {
  if (processing) return;
  processing = true;
  while (queue.length > 0) {
    const { title, resolve } = queue.shift();
    const key = CACHE_PREFIX + normalizeTitle(title);
    const stored = await browser.storage.local.get(key);
    if (stored[key] !== undefined) {
      resolve(stored[key]);
    } else {
      resolve(await fetchRating(title));
      if (queue.length > 0) await sleep(REQUEST_DELAY_MS);
    }
  }
  processing = false;
}

async function getToken() {
  if (ftoken) return ftoken;
  try {
    const resp = await fetch(FA_MAIN, { credentials: 'include' });
    const html = await resp.text();
    const match = html.match(/['"]([\da-f]{64})['"]/);
    if (match) ftoken = match[1];
  } catch (_) {}
  return ftoken;
}

async function fetchRating(title) {
  const key = CACHE_PREFIX + normalizeTitle(title);
  const stored = await browser.storage.local.get(key);
  if (stored[key] !== undefined) return stored[key];

  const empty = { foundTitle: null, rating: null, filmUrl: null };

  try {
    const token = await getToken();
    const body = new URLSearchParams({ dataType: 'json', term: title, ...(token ? { ftoken: token } : {}) });

    const acResp = await fetch(AC_URL, {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'X-Requested-With': 'XMLHttpRequest',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
      },
      body: body.toString(),
    });

    if (!acResp.ok) {
      await browser.storage.local.set({ [key]: empty });
      return empty;
    }

    const data = await acResp.json();
    const movies = data?.results?.movies;
    if (!movies || movies.length === 0) {
      await browser.storage.local.set({ [key]: empty });
      return empty;
    }

    const filmUrl = `https://www.filmaffinity.com/es/film${movies[0].id}.html`;
    const filmResp = await fetch(filmUrl, { credentials: 'include' });
    if (!filmResp.ok) {
      await browser.storage.local.set({ [key]: empty });
      return empty;
    }

    const filmDoc = new DOMParser().parseFromString(await filmResp.text(), 'text/html');
    const result = {
      foundTitle: filmDoc.querySelector('h1#main-title span[itemprop="name"]')?.textContent.trim() ?? null,
      rating: filmDoc.querySelector('#movie-rat-avg')?.textContent.trim() ?? null,
      filmUrl,
    };

    await browser.storage.local.set({ [key]: result });
    return result;
  } catch (_) {
    return empty;
  }
}

function normalizeTitle(title) {
  return title.toLowerCase().replace(/[^a-z0-9]/g, '_');
}

function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}
