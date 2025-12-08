// Copyright 2025 The MathWorks, Inc.
module.exports = {
  preset: "ts-jest",
  testEnvironment: "node",
  testMatch: ["src/tests/**/*.ts?(x)", "**/?(*.)+(spec|test).ts?(x)"],
  testPathIgnorePatterns: ["/node_modules/", "/src/tests/jest-setup.ts"],
  moduleFileExtensions: ["ts", "tsx", "js", "jsx", "json", "node"],
  setupFilesAfterEnv: ["<rootDir>/src/tests/jest-setup.ts"],
  transform: {
    "^.+\\.(ts|tsx)$": "ts-jest",
  },
  transformIgnorePatterns: [
    "/node_modules/(?!(@jupyterlab)/)", // Transform @jupyterlab packages
  ],
  moduleNameMapper: {
    // Mock @jupyterlab/ui-components to avoid ES modules issues
    "@jupyterlab/ui-components": "<rootDir>/src/tests/mocks/ui-components.js",
  },
};
