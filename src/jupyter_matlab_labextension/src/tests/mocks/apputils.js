// Copyright 2025-2026 The MathWorks, Inc.

// Mock for @jupyterlab/apputils
module.exports = {
    // Mock the Notification object/namespace
    Notification: {
        // Mock the static methods like .info(), .error(), etc.
        // They return an IDisposable, which just has a .dispose() method.
        info: jest.fn(() => ({ dispose: jest.fn() })),
        success: jest.fn(() => ({ dispose: jest.fn() })),
        warning: jest.fn(() => ({ dispose: jest.fn() })),
        error: jest.fn(() => ({ dispose: jest.fn() }))
    },

    // Mock the ToolbarButtonclass
    ToolbarButton: jest.fn().mockImplementation((options) => ({
        ...options,
        node: {
            getBoundingClientRect: jest.fn(() => ({
                left: 10,
                bottom: 20
            }))
        },
        dispose: jest.fn()
    }))

    // Add mocks for any other things you import from @jupyterlab/apputils
    // For example, if you use the default export or other items:
    // default: jest.fn(),
    // MainAreaWidget: jest.fn(),
};
