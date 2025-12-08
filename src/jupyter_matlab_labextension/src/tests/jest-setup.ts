// Copyright 2025 The MathWorks, Inc.

// Mock global objects that might not be available in the Node.js environment

// Mock window object if needed
// Tests run in a node environment, where 'window' is not defined.
// This mock ensures that 'window' is defined during tests.
if (typeof window === 'undefined') {
    (global as any).window = {
        open: jest.fn()
    };
}

// Reset mocks before each test
beforeEach(() => {
    jest.clearAllMocks();
});
