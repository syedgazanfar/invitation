// Node 22+ defines its own (flag-gated, here undefined) `localStorage` global,
// which shadows jsdom's. Point the globals back at jsdom's storage.
const dom = (globalThis as unknown as { jsdom?: { window: Window } }).jsdom;
if (dom) {
  for (const key of ['localStorage', 'sessionStorage'] as const) {
    Object.defineProperty(globalThis, key, { value: dom.window[key], configurable: true, writable: true });
  }
}
