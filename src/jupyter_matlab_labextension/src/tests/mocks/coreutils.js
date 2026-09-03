// Copyright 2025-2026 The MathWorks, Inc.

// Mock for @jupyterlab/coreutils
module.exports = {
    // Mock the PageConfig object
    PageConfig: {
        getBaseUrl: jest.fn().mockReturnValue('http://localhost:8888/')
    }
};
