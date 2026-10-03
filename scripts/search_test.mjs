import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import { existsSync, readFileSync } from 'node:fs';
import vm from 'node:vm';

const source = new URL('../static/search.js', import.meta.url);
assert.ok(existsSync(source), 'Search implementation must exist');
const search = createRequire(import.meta.url)(source.pathname);
assert.equal(typeof search.normalize, 'function');
assert.equal(search.normalize('Café'), search.normalize('Cafe\u0301'));
assert.equal(search.normalize('İ I i ı'), 'i i i i');
assert.equal(search.normalize('ÇĞÖŞÜ résumé'), 'cgosu resume');
assert.equal(search.normalize(null), '');
assert.equal(search.normalize({}), '');
assert.equal(typeof search.safeURL, 'function');
const origin = 'https://aja.example';
for (const url of ['/posts/one/', '/a?q=hello#part', '/caf%C3%A9/', '/a%20b/']) {
  assert.equal(search.safeURL(url, origin), url, `accept ${url}`);
}
for (const url of [null, {}, '', 'relative', 'https://aja.example/a', 'https://evil.example',
  'javascript:alert(1)', 'data:text/html,bad', '//evil.example', '/\\evil.example',
  '\\evil.example', '/\n/evil.example', '/\tfoo', '/\u0000foo', '/\u007ffoo',
  '/%2fevil.example', '/%5cevil.example', '/%252fevil.example', '/%255cevil.example',
  '/%00foo', '/%0Afoo', '/%7ffoo', '/bad%escape', '/bad%', '/ok\\bad']) {
  assert.equal(search.safeURL(url, origin), null, `reject ${JSON.stringify(url)}`);
}
for (let codepoint = 0; codepoint < 32; codepoint += 1) {
  const control = String.fromCharCode(codepoint);
  const escape = '%' + codepoint.toString(16).padStart(2, '0');
  assert.equal(search.safeURL('/a' + control + 'b', origin), null);
  assert.equal(search.safeURL('/a' + escape + 'b', origin), null);
}
assert.equal(search.safeURL('/%C2%85', origin), null);
assert.equal(search.safeURL('/safe', 'not an origin'), null);
assert.equal(search.safeURL('/safe', 'file:///local'), null);
assert.equal(typeof search.find, 'function');
const entry = (url, fields = {}) => ({ title: 'Other', description: '', content: '', tags: [], date: '2026-10-03', url, ...fields });
const index = [
  entry('/body', { content: 'alpha beta' }),
  entry('/tag', { tags: ['alpha beta'] }),
  entry('/description', { description: 'alpha beta' }),
  entry('/z-title', { title: 'alpha beta' }),
  entry('/a-title', { title: 'alpha beta' }),
  entry('/split', { title: 'alpha', content: 'beta' }),
  entry('/missing', { title: 'alpha' }),
];
assert.deepEqual(search.find(index, 'alpha beta').map(item => item.url),
  ['/a-title', '/z-title', '/split', '/description', '/tag', '/body']);
assert.deepEqual(search.find(index, '  BETA  alpha alpha ').map(item => item.url),
  search.find(index, 'alpha beta').map(item => item.url));
assert.deepEqual(search.find(index, ''), []);
assert.deepEqual(search.find(index, '   '), []);
assert.deepEqual(search.find(index, null), []);
assert.deepEqual(search.find(index, 'absent'), []);
assert.deepEqual(search.find(null, 'alpha'), []);
assert.deepEqual(search.find({}, 'alpha'), []);
assert.equal(search.find([entry('/accent', { title: 'İstanbul Café' })], 'ıSTANBUL cafe\u0301').length, 1);
const code = '<img src=x onerror=alert(1)> [a-z]+ .* (foo)';
assert.equal(search.find([entry('/literal', { content: code })], code).length, 1);
assert.deepEqual(search.find(index, '[a-z]+'), []);
assert.deepEqual(search.find(index, '.*'), []);
assert.deepEqual(search.find([null, {}, 7, [], { title: 'alpha', url: '//evil.example' },
  { title: null, url: '/bad' }, { title: '', url: '/bad' },
  entry('/okay', { title: 'alpha', tags: [null, {}, 3], description: {}, content: 3, date: {} })], 'alpha').map(item => item.url), ['/okay']);
assert.equal(JSON.stringify(index), JSON.stringify([
  entry('/body', { content: 'alpha beta' }), entry('/tag', { tags: ['alpha beta'] }),
  entry('/description', { description: 'alpha beta' }), entry('/z-title', { title: 'alpha beta' }),
  entry('/a-title', { title: 'alpha beta' }), entry('/split', { title: 'alpha', content: 'beta' }),
  entry('/missing', { title: 'alpha' }),
]), 'find must not mutate the index');
// A deliberately small DOM: dangerous HTML sinks throw instead of silently passing.
class Element {
  constructor(tag) { this.tagName = tag; this.children = []; this.events = {}; this.value = ''; this.attributes = {}; this.text = ''; }
  set innerHTML(_) { throw new Error('Unsafe HTML sink'); }
  set textContent(value) { this.text = String(value); this.children = []; }
  get textContent() { return this.text + this.children.map(child => child.textContent).join(''); }
  appendChild(child) { this.children.push(child); return child; }
  setAttribute(name, value) { this.attributes[name] = String(value); }
  addEventListener(name, handler) { (this.events[name] ||= []).push(handler); }
  dispatch(name, event = {}) { for (const handler of this.events[name] || []) handler(event); }
}
const script = readFileSync(source, 'utf8');
function browser(query = '?q=alpha&keep=1#anchor', readyState = 'complete') {
  const nodes = Object.fromEntries(['search-form', 'search-query', 'search-status', 'search-results'].map(id => [id, new Element(id)]));
  const document = { readyState, events: {}, getElementById: id => nodes[id], createElement: tag => new Element(tag),
    addEventListener(name, handler) { this.events[name] = handler; } };
  const location = new URL('/search/' + query, origin);
  const historyCalls = [];
  let resolveFetch;
  let rejectFetch;
  const requests = [];
  const context = { document, location, URL, URLSearchParams, console,
    history: { state: { saved: true }, replaceState(state, _, url) { historyCalls.push({ state, url }); location.href = new URL(url, location).href; } },
    fetch(url) { requests.push(url); return new Promise((resolve, reject) => { resolveFetch = resolve; rejectFetch = reject; }); } };
  vm.runInNewContext(script, context, { filename: 'search.js' });
  return { nodes, context, document, location, requests, historyCalls,
    resolve(data, ok = true) { resolveFetch({ ok, json: async () => data }); },
    malformed() { resolveFetch({ ok: true, json: async () => { throw new SyntaxError('bad json'); } }); },
    reject() { rejectFetch(new Error('offline')); } };
}
const tick = () => new Promise(resolve => setImmediate(resolve));
const page = browser();
assert.equal(page.nodes['search-query'].value, 'alpha', 'initialize input from ?q=');
assert.deepEqual(page.requests, ['/search.json']);
assert.match(page.nodes['search-status'].textContent, /loading/i);
page.nodes['search-query'].value = 'beta';
page.nodes['search-query'].dispatch('input');
page.nodes['search-query'].value = 'literal';
page.nodes['search-query'].dispatch('input');
assert.equal(page.location.searchParams.get('q'), 'literal');
assert.equal(page.location.searchParams.get('keep'), '1');
assert.equal(page.location.hash, '#anchor');
page.resolve([entry('/alpha', { title: 'alpha' }), entry('/beta', { title: 'beta' }),
  entry('/literal', { title: 'literal <script>alert(1)</script>', description: code }),
  entry('//evil.example', { title: 'literal' })]);
await tick();
assert.equal(page.nodes['search-results'].children.length, 1, 'latest query wins during loading');
const result = page.nodes['search-results'].children[0];
assert.equal(result.children[0].tagName, 'a');
assert.equal(result.children[0].href, '/literal');
assert.equal(result.children[0].textContent, 'literal <script>alert(1)</script>');
assert.ok(result.textContent.includes(code), 'untrusted description rendered as text');
assert.ok(result.textContent.includes('2026-10-03'), 'date rendered');
assert.match(page.nodes['search-status'].textContent, /1 result/i);
let prevented = false;
page.nodes['search-query'].value = 'missing';
page.nodes['search-form'].dispatch('submit', { preventDefault() { prevented = true; } });
assert.ok(prevented);
assert.equal(page.location.searchParams.get('q'), 'missing');
assert.match(page.nodes['search-status'].textContent, /no results/i);
assert.equal(page.nodes['search-results'].children.length, 0);
page.nodes['search-query'].value = '';
page.nodes['search-query'].dispatch('input');
assert.equal(page.location.searchParams.has('q'), false);
assert.match(page.nodes['search-status'].textContent, /enter|type/i);
const excerptPage = browser('?q=needle');
excerptPage.resolve([entry('/body', { content: 'needle ' + 'body '.repeat(100) }),
  entry('/other', { title: 'needle', date: {}, description: null })]);
await tick();
assert.match(excerptPage.nodes['search-status'].textContent, /2 results/i);
const bodyResult = excerptPage.nodes['search-results'].children.find(item => item.children[0].href === '/body');
assert.match(bodyResult.textContent, /needle/);
assert.ok(bodyResult.textContent.length < 350, 'body excerpt bounded');
for (const failure of ['reject', 'malformed', 'shape', 'http']) {
  const broken = browser();
  if (failure === 'reject') broken.reject();
  else if (failure === 'malformed') broken.malformed();
  else if (failure === 'shape') broken.resolve({ entries: [] });
  else broken.resolve([], false);
  await tick();
  assert.match(broken.nodes['search-status'].textContent, /could not|unable|failed/i, failure);
  assert.equal(broken.nodes['search-results'].children.length, 0);
}
const late = browser('?q=alpha', 'loading');
assert.equal(late.requests.length, 0);
late.document.events.DOMContentLoaded();
assert.equal(late.requests.length, 1);
late.resolve([]);
await tick();
assert.match(late.nodes['search-status'].textContent, /no results/i);
const emptyPage = browser('');
emptyPage.resolve([]);
await tick();
assert.match(emptyPage.nodes['search-status'].textContent, /enter|type/i);
assert.equal(emptyPage.nodes['search-status'].attributes.role, 'status');
assert.equal(emptyPage.nodes['search-status'].attributes['aria-live'], 'polite');
const restrictedHistory = browser('?q=alpha');
restrictedHistory.context.history.replaceState = () => { throw new Error('restricted'); };
restrictedHistory.resolve([entry('/alpha', { title: 'alpha' })]);
await tick();
restrictedHistory.nodes['search-query'].dispatch('input');
assert.equal(restrictedHistory.nodes['search-results'].children.length, 1);
const minimal = { URL, URLSearchParams };
vm.runInNewContext(script, minimal);
assert.equal(typeof minimal.AjaSearch.find, 'function', 'safe without a document');
console.log('Search tests passed');
