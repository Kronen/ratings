const CARD_SELECTOR = '.title-card';
const DELAY_BEFORE_FETCH_MS = 800; // wait briefly after card enters view before queuing

const processed = new WeakSet();
const intersectionObserver = new IntersectionObserver(onCardsVisible, { threshold: 0.5 });
const mutationObserver = new MutationObserver(onDomChange);

function isValidTitle(title) {
  if (!title || title.length < 2 || title.length > 120) return false;
  // Reject date strings like "May 4, 2026"
  if (/^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d+,?\s*\d{4}$/.test(title)) return false;
  return true;
}

function extractTitle(card) {
  const anchor = card.querySelector('a[aria-label]');
  if (anchor) return anchor.getAttribute('aria-label');
  if (card.getAttribute('aria-label')) return card.getAttribute('aria-label');
  const fallback = card.querySelector('.fallback-text');
  if (fallback) return fallback.textContent.trim();
  return null;
}

function colorClass(ratingText) {
  if (!ratingText) return 'fa-grey';
  const n = parseFloat(ratingText.replace(',', '.'));
  if (isNaN(n)) return 'fa-grey';
  if (n >= 7) return 'fa-green';
  if (n >= 5) return 'fa-yellow';
  return 'fa-red';
}

function onCardsVisible(entries) {
  for (const entry of entries) {
    if (!entry.isIntersecting) continue;
    const card = entry.target;
    intersectionObserver.unobserve(card);

    setTimeout(() => {
      if (processed.has(card)) return;
      const title = extractTitle(card);
      if (!isValidTitle(title)) return;
      processed.add(card);

      browser.runtime.sendMessage({ type: 'GET_RATING', title }).then((result) => {
        if (!result) return;
        const badge = document.createElement('div');
        badge.className = `fa-rating-badge ${colorClass(result.rating)}`;
        badge.textContent = result.rating || 'N/F';
        if (result.foundTitle) badge.title = result.foundTitle;
        if (result.filmUrl) {
          badge.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            window.open(result.filmUrl, '_blank', 'noopener,noreferrer');
          });
          badge.style.cursor = 'pointer';
        }
        card.appendChild(badge);
      });
    }, DELAY_BEFORE_FETCH_MS);
  }
}

function registerCards(root) {
  (root.querySelectorAll ? root.querySelectorAll(CARD_SELECTOR) : []).forEach((card) => {
    if (!processed.has(card)) intersectionObserver.observe(card);
  });
}

function onDomChange(mutations) {
  for (const { addedNodes } of mutations) {
    for (const node of addedNodes) {
      if (node.nodeType !== Node.ELEMENT_NODE) continue;
      registerCards(node);
    }
  }
}

mutationObserver.observe(document.body, { childList: true, subtree: true });
registerCards(document);
