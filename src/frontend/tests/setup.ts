import '@testing-library/jest-dom/vitest';

const storedValues = new Map<string, string>();
Object.defineProperty(globalThis, 'localStorage', {
  configurable: true,
  value: {
    get length() { return storedValues.size; },
    clear() { storedValues.clear(); },
    getItem(key: string) { return storedValues.get(key) ?? null; },
    key(index: number) { return [...storedValues.keys()][index] ?? null; },
    removeItem(key: string) { storedValues.delete(key); },
    setItem(key: string, value: string) { storedValues.set(String(key), String(value)); },
  } satisfies Storage,
});

Object.defineProperty(document, 'visibilityState', {
  configurable: true,
  value: 'visible',
});
