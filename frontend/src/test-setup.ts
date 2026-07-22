import "@testing-library/jest-dom";

// Polyfill ResizeObserver for Radix UI popover tests
if (typeof ResizeObserver === "undefined") {
  (globalThis as unknown as Record<string, unknown>).ResizeObserver = class ResizeObserver {
    observe() {}
    unobserve() {}
    disconnect() {}
  };
}

// Polyfill scrollIntoView for jsdom
if (typeof Element !== "undefined" && !Element.prototype.scrollIntoView) {
  Element.prototype.scrollIntoView = () => {};
}
