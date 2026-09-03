// Copyright 2025-2026 The MathWorks, Inc.

// Mock global objects that might not be available in the Node.js environment

// Tests run in a node environment, where 'window' may be undefined.
// Define only the methods required by tests to avoid replacing `window` entirely.
const globalObj = globalThis as any;
if (typeof globalObj.window === 'undefined') {
    globalObj.window = {};
}
if (typeof globalObj.window.open !== 'function') {
    globalObj.window.open = jest.fn();
}
if (typeof globalObj.window.addEventListener !== 'function') {
    globalObj.window.addEventListener = jest.fn();
}
if (typeof globalObj.window.removeEventListener !== 'function') {
    globalObj.window.removeEventListener = jest.fn();
}

// Reset mocks before each test
beforeEach(() => {
    jest.clearAllMocks();
});
