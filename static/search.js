(function (root) {
  'use strict';

  function normalize(value) {
    return typeof value === 'string'
      ? value.replace(/[İı]/g, 'i').normalize('NFD').replace(/\p{M}/gu, '').toLowerCase()
      : '';
  }

  // Fail closed on encoded separators/controls, including nested escapes.
  function safeURL(value, origin = 'https://aja.invalid') {
    if (typeof value !== 'string' || !value.startsWith('/') || value.startsWith('//')) return null;
    let decoded = value;
    try {
      for (let i = 0; i <= value.length; i += 1) {
        if (/[\\\u0000-\u0020\u007f-\u009f]/u.test(decoded) && decoded === value) {
          // Literal spaces are rejected; encoded spaces below remain valid.
          return null;
        }
        if (/[\\\u0000-\u001f\u007f-\u009f]/u.test(decoded) || decoded.startsWith('//')) return null;
        if (/%(?:2f|5c)/i.test(decoded)) return null;
        if (!decoded.includes('%')) break;
        const next = decodeURIComponent(decoded);
        if (next === decoded) break;
        decoded = next;
      }
      const base = new URL(origin);
      const parsed = new URL(value, base);
      return parsed.origin === base.origin && /^https?:$/.test(parsed.protocol) ? value : null;
    } catch (_) {
      return null;
    }
  }

  function find(index, query, origin) {
    const terms = [...new Set(normalize(query).trim().split(/\s+/u).filter(Boolean))];
    if (!Array.isArray(index) || terms.length === 0) return [];
    const matches = [];
    for (const item of index) {
      if (!item || typeof item !== 'object' || typeof item.title !== 'string' || !item.title.trim()) continue;
      if (safeURL(item.url, origin) === null) continue;
      const title = normalize(item.title);
      const description = normalize(item.description);
      const tags = Array.isArray(item.tags) ? item.tags.filter(tag => typeof tag === 'string').map(normalize).join(' ') : '';
      const content = normalize(item.content);
      let titleHits = 0;
      let summaryHits = 0;
      if (!terms.every(term => {
        if (title.includes(term)) { titleHits += 1; return true; }
        if (description.includes(term) || tags.includes(term)) { summaryHits += 1; return true; }
        return content.includes(term);
      })) continue;
      matches.push({ item, titleHits, summaryHits });
    }
    matches.sort((a, b) => b.titleHits - a.titleHits || b.summaryHits - a.summaryHits ||
      (a.item.url < b.item.url ? -1 : a.item.url > b.item.url ? 1 : 0));
    return matches.map(match => match.item);
  }

  function init() {
    const document = root.document;
    const form = document.getElementById('search-form');
    const input = document.getElementById('search-query');
    const status = document.getElementById('search-status');
    const results = document.getElementById('search-results');
    if (!form || !input || !status || !results) return;
    status.setAttribute('role', 'status');
    status.setAttribute('aria-live', 'polite');
    input.value = new URL(root.location.href).searchParams.get('q') || '';
    let index = [];
    let state = 'loading';

    function render() {
      results.textContent = '';
      if (state === 'loading') { status.textContent = 'Loading search index…'; return; }
      if (state === 'failed') {
        status.textContent = 'Search could not be loaded. Please try again later.';
        return;
      }
      if (!input.value.trim()) { status.textContent = 'Enter a search query.'; return; }
      const matches = find(index, input.value, root.location.origin);
      for (const item of matches) {
        const li = document.createElement('li');
        const link = document.createElement('a');
        link.href = safeURL(item.url, root.location.origin);
        link.textContent = item.title;
        li.appendChild(link);
        const description = typeof item.description === 'string' ? item.description.trim() : '';
        const content = typeof item.content === 'string' ? item.content.trim() : '';
        const excerpt = description || (content.length > 240 ? content.slice(0, 240) + '…' : content);
        if (excerpt) {
          const paragraph = document.createElement('p');
          paragraph.textContent = excerpt;
          li.appendChild(paragraph);
        }
        if (typeof item.date === 'string' && item.date.trim()) {
          const date = document.createElement('p');
          date.textContent = item.date;
          li.appendChild(date);
        }
        results.appendChild(li);
      }
      status.textContent = matches.length ? `${matches.length} ${matches.length === 1 ? 'result' : 'results'} found.` : 'No results found.';
    }

    function update() {
      const url = new URL(root.location.href);
      if (input.value.trim()) url.searchParams.set('q', input.value);
      else url.searchParams.delete('q');
      try {
        root.history.replaceState(root.history.state, '', url.pathname + url.search + url.hash);
      } catch (_) {
        // Restricted history must not prevent local search from working.
      }
      render();
    }

    input.addEventListener('input', update);
    form.addEventListener('submit', event => { event.preventDefault(); update(); });
    render();
    // Read the live input after completion: typing never gets lost during fetch.
    (async () => {
      const response = await root.fetch('/search.json');
      if (!response.ok) throw new Error('Search request failed');
      const data = await response.json();
      if (!Array.isArray(data)) throw new Error('Invalid search index');
      index = data;
      state = 'ready';
      render();
    })().catch(() => { state = 'failed'; render(); });
  }

  const api = { normalize, safeURL, find };
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.AjaSearch = api;
  if (root.document) {
    if (root.document.readyState === 'loading') root.document.addEventListener('DOMContentLoaded', init, { once: true });
    else init();
  }
})(globalThis);
